## Setting up DREAM challenge for python


### Cloning challenge templates
```
git clone https://github.com/Sage-Bionetworks/SynapseChallengeTemplates.git
```

### Setting up a DREAM challenge wikipage

All DREAM challenges should have a live and staging site.  To start, please create two synapse projects (Click [here](http://docs.synapse.org/articles/making_a_project.html) if you don't know how to set up a synapse project).  The two projects should be named something like this:  "Your DREAM challenge" and "Your DREAM challenge staging site".  It is important to note that the live site will act as a splash site as the DREAM challenge is in development.  **All edits and changes even after the challenge has launched should be made on the staging site**

To set up a DREAM challenge synapse wikipage, navigate to `SynapseChallengeTemplates/createChallengeWiki.command` and double click the script.  This script will prompt you to login to synapse and give it a synapse project Id so that it can copy the template over.  If you have the python synapseclient (develop), you can follow these instructions to copy the template to your project.  This page will most likely act as the staging site.

```
import synapseclient
import synapseutils as synu

syn = synapseclient.login()
synu.cp(syn, "syn2769515", "Your project synapse Id goes here")
```

### Setting up a DREAM challenge infrastructure
** Teams required **

All challenges require a challenge participant, challenge pre-registrant, and administrator team.  To learn how to set up synapse teams, please learn more about teams [here](http://docs.synapse.org/articles/teams.html).

** Registering the challenge team to the challenge site (creating challengeId)**

```
import json
challenge_object = {'id': u'1000',
 'participantTeamId': u'1111', #Your participant team
 'projectId': u'syn12345'} #your challenge site
syn.restPOST('/challenge', challenge_object)
```
After doing this you will be able to access the challengeId by doing
```
challenge = syn.restGET('/entity/syn12345/challenge')
challenge.id
```

Make sure to replace all the places that have `challengeId` in the staging site (3.2 - Forming a team)

** 
