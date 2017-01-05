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


config_evaluations = [
#Sub-Challenge 1 (12345)
#Sub-Challenge 2 (23456)
    {
        'id':12345,
        'score_sh':'/score_sc1.sh'
    },
    {
        'id':23456,
        'score_sh':'/score_sc2.sh'
    }

]

config_evaluations_map = {ev['id']:ev for ev in config_evaluations}



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
        raise(e)

    # must use os.system (Can't pipe with subprocess)
    out = os.system('docker run -it --rm -e="CLI=true" %s [ -e %s ] || (echo "DoesNotExist" && exit 1)' % (dockerImage, scoring_sh))
    assert out==0, "%s must exist for your docker container to run" % scoring_sh

    predFolder = syn.store(Folder(submission.id, parent = CHALLENGE_LOG_PREDICTION_FOLDER))
    for participant in submission.contributors:
        syn.setPermissions(predFolder, principalId = participant['principalId'], accessType = adminAccess)

    return(True, "Your submission has been validated!  As your submission is being scored, please go here: https://www.synapse.org/#!Synapse:%s to check on your log files and resulting prediction files." % predFolder.id)

def dockerRun(submission, containerName = None):
    #grab folder where logs/predictions are stored
    predFolder = syn.query('select id from folder where parentId == "%s" and name == "%s"' % (CHALLENGE_LOG_PREDICTION_FOLDER,submission.id))
    predFolderId = predFolder['results'][0]['folder.id']

    dockerDigest = submission.get('dockerDigest')
    submissionJson = json.loads(submission['entityBundleJSON'])
    dockerRepo = submissionJson['entity']['repositoryName']
    dockerImage = dockerRepo + "@" + dockerDigest

    #Mount volumes
    volumes = {}
    for vol in ALL_VOLUMES:
        volumes[vol] = {'bind': MOUNTED_VOLUMES[vol].split(":")[0], 'mode': MOUNTED_VOLUMES[vol].split(":")[1]}

    # Run docker image (Can attach container name if necessary)
    container = client.containers.run(dockerRepo, 'bash %s' % scoring_sh, detach=True,volumes = volumes)
    
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
                ent = File(LogFileName, parent = predFolderId)
                logs = syn.store(ent)

    #Remove container after being done
    container.remove()

    #Zip up predictions and store it into CHALLENGE_PREDICTIONS_FOLDER
    zipf = zipfile.ZipFile(submission.id + '_predictions.zip', 'w', zipfile.ZIP_DEFLATED)
    zipdir(OUTPUT_DIR, zipf)
    zipf.close()

    ent = File(submission.id + '_predictions.zip', parent = predFolder.id)
    predictions = syn.store(ent)
    return(predictions.id, logs.id)


def validate_docker(evaluation, submission):
	"""
	Find the right validation function and validate the submission.

	:returns: (True, message) if validated, (False, message) if
			  validation fails or throws exception
	"""
    config = config_evaluations_map[int(evaluation.id)]

    results = dockerValidate(submission, config['score_sh'], syn, client)
	return(results)


def run_docker(evaluation, submission):
	"""
	Find the right scoring function and score the submission

	:returns: (score, message) where score is a dict of stats and message
			  is text for display to user
	"""
    config = config_evaluations_map[int(evaluation.id)]

    prediction_synId, log_synId =  dockerRun(submission,config['score_sh'], syn, client)
    return (dict(predictions=prediction_synId, log_synId = log_synId), "You did fine!")
