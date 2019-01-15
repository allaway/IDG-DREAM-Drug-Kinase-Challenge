#!/usr/bin/env cwl-runner

cwlVersion: v1.0
class: CommandLineTool
baseCommand: [Rscript, /usr/local/bin/validate.R]

requirements:
- class: InlineJavascriptRequirement

hints:
  DockerRequirement:
    dockerPull: quay.io/andrewelamb/drug_target_validate_1b
    
inputs:

  submission_file:
    type: File
    inputBinding:
      prefix: --submission_file
  
  goldstandard:
    type: File
    inputBinding:
      prefix: --gold_standard

outputs:

  - id: results
    type: File
    outputBinding:
      glob: "results.json"
      
  - id: status
    type: string
    outputBinding:
      glob: "results.json"
      loadContents: true
      outputEval: $(JSON.parse(self[0].contents)['prediction_file_status'])

  - id: invalid_reasons
    type: string
    outputBinding:
      glob: "results.json"
      loadContents: true
      outputEval: $(JSON.parse(self[0].contents)['prediction_file_errors'])
