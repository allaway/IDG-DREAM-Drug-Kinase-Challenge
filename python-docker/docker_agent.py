import docker
import json
import subprocess
from synapseclient import File
import zipfile
import os

#Synapse Id of Challenge
CHALLENGE_SYN_ID = "syn4586419"
#Synapse Id of directory that you want the log files to go into
CHALLENGE_LOG_FOLDER = "syn4990358"
CHALLENGE_PREDICTION_FOLDER = "syn4990358"
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
ADMIN_USER_IDS = ["3324230"]


evaluation_queues = [
	{'status': u'OPEN', 'contentSource': u'syn4586419', 'submissionInstructionsMessage': u'To submit to the XYZ Challenge, send a tab-delimited file as described here: https://...', u'createdOn': u'2015-07-01T18:41:43.295Z', 'submissionReceiptMessage': u'Your submission has been received. For further information, consult the leader board at https://...', u'etag': u'a595f04a-c5a2-4b0e-8d1f-003a8c46c0cd', u'ownerId': u'3324230', u'id': u'4586421', 'name': u'Example Synapse Challenge 4f41d8a1-8200-4030-97ae-352bc03577b6'}]
evaluation_queue_by_id = {q['id']:q for q in evaluation_queues}


def zipdir(path, ziph):
	# ziph is zipfile handle
	for root, dirs, files in os.walk(path):
		for file in files:
			ziph.write(os.path.join(root, file),os.path.join(root, file).replace(path+"/",""))

def dockerValidate(submission):
	assert submission.get('dockerDigest') is not None, "Must submit a docker container"
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

	#MUST ADD PERMISSIONS SO PARTICIPANTS CAN SEE THEIR OWN LOG FILE/PREDICTIONS


	#Zip up predictions and store it into CHALLENGE_PREDICTIONS_FOLDER
	zipf = zipfile.ZipFile(submission.id + '_predictions.zip', 'w', zipfile.ZIP_DEFLATED)
	zipdir(OUTPUT_DIR, zipf)
	zipf.close()

	ent = File(submission.id + '_predictions.zip', parent = CHALLENGE_PREDICTION_FOLDER)
	predictions = syn.store(ent)
	return(predictions.id, logs.id)


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
	return (dict(predictions=prediction_synId, log_synId = log_synId), "You did fine!")
