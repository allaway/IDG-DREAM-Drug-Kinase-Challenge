#!/usr/bin/env cwl-runner
#
# annotate an existing submission with a string value
# (variations can be written to pass long or float values)
#
cwlVersion: v1.0
class: CommandLineTool
baseCommand: python

inputs:
  - id: submissionId
    type: int
  - id: annotationValues
    type: File
  - id: private
    type: string
  - id: synapseConfig
    type: File

arguments:
  - valueFrom: annotationSubmission.py
  - valueFrom: $(inputs.submissionId)
    prefix: -s
  - valueFrom: $(inputs.annotationValues)
    prefix: -v
  - valueFrom: $(inputs.private)
    prefix: -p
  - valueFrom: $(inputs.synapseConfig.path)
    prefix: -c

requirements:
  - class: InlineJavascriptRequirement
  - class: InitialWorkDirRequirement
    listing:
      - entryname: annotationSubmission.py
        entry: |
          #!/usr/bin/env python
          import synapseclient
          import argparse
          import json
          if __name__ == '__main__':
            parser = argparse.ArgumentParser()
            parser.add_argument("-s", "--submissionId", required=True, help="Submission ID")
            parser.add_argument("-v", "--annotationValues", required=True, help="Name of annotation to add")
            parser.add_argument("-p", "--private", required=False, help="Annotation is private to queue administrator(s)")
            parser.add_argument("-c", "--synapseConfig", required=True, help="credentials file")
            args = parser.parse_args()

            syn = synapseclient.Synapse(configPath=args.synapseConfig)
            syn.login()
            status = syn.getSubmissionStatus(args.submissionId)
            with open(args.annotationValues) as json_data:
              annots = json.load(json_data)
            status.status = annots['status']
            del annots['status']
            subAnnots = synapseclient.annotations.to_submission_status_annotations(annots,is_private=args.private)
            status.annotations = subAnnots
            status = syn.store(status)
     
outputs: []

