#!/usr/bin/env python2

# Import AWS Scout2 finding-related classes
from AWSScout2.finding_cloudtrail import *
from AWSScout2.finding_ec2 import *
from AWSScout2.finding_iam import *
from AWSScout2.finding_s3 import *
from AWSScout2.utils import *

import copy
import re


########################################
# Finding dictionaries
########################################
cloudtrail_finding_dictionary = {}
iam_finding_dictionary = {}
ec2_finding_dictionary = {}
s3_finding_dictionary = {}


########################################
# Common functions
########################################

def load_findings(service, ruleset_name, customize = False):

    # Load rules from JSON file
    try:
        if type(ruleset_name) == list:
            ruleset_name = ruleset_name[0]
        filename = 'rules/findings-' + service + '.' + ruleset_name + '.json'
        with open(filename) as f:
            findings = json.load(f)
    except Exception, e:
        print 'Error: the ruleset name entered (%s) does not match an existing configuration.' % ruleset_name
        return

    # Special case
    if ruleset_name == 'custom':
        customize = True

    # Parse and customize rules
    for f in findings:
        questions = findings[f]['questions'] if 'questions' in findings[f] else []
        if 'targets' in findings[f]:
            for t in findings[f]['targets']:
                name = set_argument_values(f, t)
                new_questions = []
                for q in questions:
                    new_questions.append(set_argument_values(q, t))
                description = set_argument_values(findings[f]['description'], t)
                entity = set_argument_values(findings[f]['entity'], t)
                callback = findings[f]['callback']
                callback_args = set_arguments(findings[f]['callback_args'], t)
                level = set_argument_values(findings[f]['level'], t)

                new_finding(service, customize, name,
                    description,
                    entity,
                    callback,
                    callback_args,
                    level,
                    new_questions)

        else:
            new_finding(service, customize, f,
                findings[f]['description'],
                findings[f]['entity'],
                findings[f]['callback'],
                findings[f]['callback_args'],
                findings[f]['level'],
                questions)

def new_finding(service, customize, key, description, entity, callback_name, callback_args, level, questions):

    # Based on the service name, determine the finding dictionary and class
    finding_dictionary, finding_class = get_finding_variables(service)

    # If this is a custom rule, prompt users for answers
    if customize and questions and len(questions):
        print ''
        activate_rule_question = questions.pop(0)
        if prompt_4_yes_no(activate_rule_question):
            for q in questions:
                answer = prompt_4_value(q)
                callback_args.append(answer)
        else:
            return

    # Save the rule in the finding dictionary
    finding_dictionary[key] = finding_class(description, entity, callback_name, callback_args, level, questions)

def set_arguments(arg_names, t):
    real_args = []
    for a in arg_names:
        real_args.append(set_argument_values(a, t))
    return real_args

def set_argument_values(string, target):
    args = re.findall(r'(_ARG_(\w+)_)', string)
    for arg in args:
        index = int(arg[1])
        string = string.replace(arg[0], target[index])
    return string

def get_finding_variables(keyword):
    if keyword == 'ec2':
        return ec2_finding_dictionary, Ec2Finding
    elif keyword == 'iam':
        return iam_finding_dictionary, IamFinding
    elif keyword == 's3':
        return s3_finding_dictionary, S3Finding
    elif keyword == 'cloudtrail':
        return cloudtrail_finding_dictionary, CloudTrailFinding
    else:
        return None, None
