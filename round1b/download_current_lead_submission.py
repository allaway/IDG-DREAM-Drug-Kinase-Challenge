import synapseclient
import challengeutils
import argparse
import os


def get_submitterid_from_submission_id(submissionid, queue, synapse_object, allowed_statuses = ["VALIDATED"]):
    query = "select * from " + queue + " where objectId == " + str(submissionid)
    generator = challengeutils.utils.evaluation_queue_query(synapse_object, query)
    lst = list(generator)
    if len(lst) == 0:
        raise Exception('submission id {} not in queue'.format(submissionid))
    submission_dict = lst[0]
    status = submission_dict['status']
    if status not in allowed_statuses:
        raise Exception('submission status not valid: {}'.format(status))
    submitterid = submission_dict['submitterId']
    return(submitterid)

def get_submitters_lead_submission(submitterid, queue, synapse_object):
    query = ("select * from " + queue + " where submitterId == " + 
             str(submitterid) + "and status == 'SCORED' and 'met_cutoff' == 'true'" +
             "order by createdOn DESC")
    generator = challengeutils.utils.evaluation_queue_query(syn, query)
    lst = list(generator)
    if len(lst) > 0:
        sub_dict = lst[0]
        object_id = sub_dict['objectId']
        sub = syn.getSubmission(object_id, downloadLocation=".")
        return(sub.filePath)
    else:
        return(NULL)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--submissionid", required=True, help="Int, or str(int) for submissionid, of current submission.")
    parser.add_argument("-q", "--queue", required=True, help="string of evaluation queue, such as evaluation_1")
    parser.add_argument("-c", "--synapse_config", required=True, help="credentials file")
    parser.add_argument("-s", "--status", required=True, help="Submission status")
    args = parser.parse_args()
    
    if args.status == "VALIDATED":
        syn = synapseclient.Synapse(configPath=args.synapse_config)
        syn.login()
        submitterid = get_submitterid_from_submission_id(args.submissionid, args.queue, syn)
        path = get_submitters_lead_submission(submitterid, args.queue, syn)
    
    
