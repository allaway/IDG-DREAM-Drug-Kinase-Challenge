# Automation of validation and scoring
script_dir=$(dirname $0)
if [ ! -d "$script_dir/log" ]; then
  mkdir $script_dir/log
fi
#---------------------
#Validate submissions
#---------------------
#Remove --send-messages to do rescoring without sending emails to participants
python3 IDG-DREAM-Drug-Kinase-Challenge/python/scoring_harness/challenge.py  --send-messages --notifications validate --all >> log/score.log 2>&1

#--------------------
#Score submissions
#--------------------
python3 IDG-DREAM-Drug-Kinase-Challenge/python/scoring_harness/challenge.py --send-messages --notifications score --all >> log/score.log 2>&1
