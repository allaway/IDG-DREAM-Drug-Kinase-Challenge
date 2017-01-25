import docker
import json
import subprocess
from synapseclient import File
import zipfile
import os

#Synapse Id of Challenge
CHALLENGE_SYN_ID = "syn1235"
#Synapse Id of directory that you want the log files to go into
CHALLENGE_LOG_FOLDER = "syn12345"
CHALLENGE_PREDICTION_FOLDER = "syn1235"
#These are the volumes that you want to mount onto your docker container
OUTPUT_DIR = '/home/ubuntu/output'
TESTDATA_DIR = '/home/ubuntu/test-data'
#These are the locations on the docker that you want your mounted volumes to be + permissions in docker (ro, rw)
#It has to be in this format '/output:rw'
MOUNTED_VOLUMES = {OUTPUT_DIR:'/output:rw',
				   TESTDATA_DIR:'/test-data:ro'}
#All mounted volumes here in a list
ALL_VOLUMES = [OUTPUT_DIR,TESTDATA_DIR]

## Name of your challenge, defaults to the name of the challenge's project
CHALLENGE_NAME = "Example Synapse Challenge"

## Synapse user IDs of the challenge admins who will be notified by email
## about errors in the scoring script
ADMIN_USER_IDS = ['123234']


evaluation_queues = [
	{'status': u'OPEN', 'contentSource': u'syn4586419', 'submissionInstructionsMessage': u'To submit to the XYZ Challenge, send a tab-delimited file as described here: https://...', u'createdOn': u'2015-07-01T18:41:43.295Z', 'submissionReceiptMessage': u'Your submission has been received. For further information, consult the leader board at https://...', u'etag': u'a595f04a-c5a2-4b0e-8d1f-003a8c46c0cd', u'ownerId': u'3324230', u'id': u'4586421', 'name': u'Example Synapse Challenge 4f41d8a1-8200-4030-97ae-352bc03577b6'}]
evaluation_queue_by_id = {q['id']:q for q in evaluation_queues}


def zipdir(path, ziph):
	# ziph is zipfile handle
	for root, dirs, files in os.walk(path):
		for file in files:
			ziph.write(os.path.join(root, file),os.path.join(root, file).replace(path+"/",""))

def dockerValidate(submission):
    submissionJson = json.loads(submission['entityBundleJSON'])
    assert submissionJson['entity'].get('repositoryName') is not None, "Must submit a docker container"
    dockerRepo = submissionJson['entity']['repositoryName']
    #assert dockerRepo.startswith("docker.synapse.org")
    assert submission.get('dockerDigest') is not None, "Must submit a docker container with a docker sha digest"
    dockerDigest = submission['dockerDigest']
    dockerImage = dockerRepo + "@" + dockerDigest

    #Check if docker is able to be pulled
    try:
        client.images.pull(dockerImage)
    except docker.errors.ImageNotFound as e:
        raise AssertionError("Docker pull failed: "+str(e))

    # must use os.system (Can't pipe with subprocess)
    out = os.system('docker run -it --rm -e="CLI=true" %s [ -e %s ] || (echo "DoesNotExist" && exit 1)' % (dockerImage, scoring_sh))
    assert out==0, "%s must exist for your docker container to run" % scoring_sh

    checkExist = syn.query('select id from folder where parentId == "%s" and name == "%s"' % (CHALLENGE_LOG_PREDICTION_FOLDER, submission.id))
    if checkExist['totalNumberOfResults'] == 0:
        predFolder = syn.store(Folder(submission.id, parent = CHALLENGE_LOG_PREDICTION_FOLDER))
        predFolder = predFolder.id
    else:
        predFolder = checkExist['results'][0]['folder.id']
    for participant in submission.contributors:
        if participant['principalId'] in ADMIN_USER_IDS: 
            access = ['CREATE', 'READ', 'UPDATE', 'DELETE', 'CHANGE_PERMISSIONS', 'MODERATE', 'CHANGE_SETTINGS']
        else:
            access = ['READ']
        syn.setPermissions(predFolder, principalId = participant['principalId'], accessType = access)
	return(True, "Looks OK to me!")


def dockerRun(submission, containerName = None):

	client = docker.from_env()
    #client.login(username, password, registry="http://docker.synapse.org")

	# MM challenge example
	submission = syn.getSubmission(7841236)
	#containerName = "testingfoo"
	dockerDigest = submission.get('dockerDigest')
	submissionJson = json.loads(submission['entityBundleJSON'])
	dockerRepo = submissionJson['entity']['repositoryName']
	dockerImage = dockerRepo + "@" + dockerDigest

	#Mount volumes
	volumes = {}
	for vol in ALL_VOLUMES:
		volumes[vol] = {'bind': MOUNTED_VOLUMES[vol].split(":")[0], 'mode': MOUNTED_VOLUMES[vol].split(":")[1]}

	# Run docker image
	container = client.containers.run(dockerRepo, 'bash /score_sc1.sh', detach=True,volumes = volumes)
	
	#Create log file
	LogFileName = submission.id + "_log.txt"
	open(LogFileName,'w+').close()
	
	#While docker is still running (the docker python client doesn't update status)
	while subprocess.Popen(['docker','inspect','-f','{{.State.Running}}',container.name],stdout = subprocess.PIPE).communicate()[0] == "true\n":
		for line in container.logs(stream=True):
			with open(LogFileName,'a') as logFile:
				logFile.write(line)
			#Only store log file if > 0bytes
			statinfo = os.stat(LogFileName)
			if statinfo.st_size > 0:
				ent = File(LogFileName, parent = CHALLENGE_LOG_FOLDER)
				logs = syn.store(ent)

	#Remove container after being done
	container.remove()
    client.images.remove(dockerImage)
    #Zip up predictions and store it into CHALLENGE_PREDICTIONS_FOLDER
    if len(os.listdir(OUTPUT_DIR)) > 0:
        zipf = zipfile.ZipFile(submission.id + '_predictions.zip', 'w', zipfile.ZIP_DEFLATED)
        zipdir(OUTPUT_DIR, zipf)
        zipf.close()

        ent = File(submission.id + '_predictions.zip', parent = predFolderId)
        predictions = syn.store(ent)
        prediction_synId = predictions.id
        os.system("rm -rf %s/*" % OUTPUT_DIR)
    else:
        prediction_synId = None
    return(prediction_synId, logs.id)


def validate_docker(evaluation, submission):
	"""
	Find the right validation function and validate the submission.

	:returns: (True, message) if validated, (False, message) if
			  validation fails or throws exception
	"""

	results = dockerValidate(submission)
	return(results)


def run_docker(evaluation, submission):
	"""
	Find the right scoring function and score the submission

	:returns: (score, message) where score is a dict of stats and message
			  is text for display to user
	"""
	prediction_synId, log_synId =  dockerRun(submission)
    if prediction_synId is not None:
        message = "You can find your prediction file here: https://www.synapse.org/#!Synapse:%s" % prediction_synId
    else:
        message = "No prediction file generated, please check your log files!"
    return (dict(PREDICTION_FILE=prediction_synId, LOG_FILE = log_synId), message)