#!/usr/bin/python
"""Late night HACK to get around bugs in current K5 Contract
   Removes K5 Load Balancers and a specific Heat Stack
   Used as script on GoCD

   Poor Quality HACK - Please don't copy :(


Author: Graham Land
Date: 25/09/17
Twitter: @allthingsclowd
Github: https://github.com/allthingsclowd
Blog: https://allthingscloud.eu


"""

import os
from time import sleep
import requests
import sys

def get_endpoint(k5token, endpoint_type):
    """Extract the appropriate endpoint URL from the K5 token object body
    Args:
        k5token (TYPE): K5 token object
        endpoint_type (TYPE): trype of endpoint required - e.g. compute, network...

    Returns:
        TYPE: string - contain the endpoint url
    """
    # list the endpoints
    for ep in k5token.json()['token']['catalog']:
        if len(ep['endpoints'])>0:
            # if this is the endpoint that  I'm looking for return the url
            if endpoint_type == ep['endpoints'][0].get('name'):
                #pprint.pprint(ep)
                return ep['endpoints'][0].get('url')

def get_scoped_token(adminUser, adminPassword, contract, projectid, region):
    """Ket a K5 project scoped token

    Args:
        adminUser (TYPE): k5 username
        adminPassword (TYPE): K5 password
        contract (TYPE): K5 contract name
        projectid (TYPE): K5 project id to scope to
        region (TYPE): K5 region

    Returns:
        TYPE: K5 token object
    """
    identityURL = 'https://identity.' + region + \
        '.cloud.global.fujitsu.com/v3/auth/tokens'

    try:
        response = requests.post(identityURL,
                                 headers={'Content-Type': 'application/json',
                                          'Accept': 'application/json'},
                                 json={"auth":
                                         {"identity":
                                          {"methods": ["password"], "password":
                                           {"user":
                                           {"domain":
                                               {"name": contract},
                                            "name": adminUser,
                                            "password": adminPassword
                                            }}},
                                          "scope":
                                          {"project":
                                           {"id": projectid
                                            }}}})

        return response
    except:
        return 'Regional Project Token Scoping Failure'

def list_load_balancers(k5token, lbaasName):
    """Summary


    Returns:
        TYPE: Description
    """
    if (lbaasName=='all'):
        lbaasURL = unicode(get_endpoint(k5token, "loadbalancing")) + unicode("/?Version=2014-11-01&Action=DescribeLoadBalancers")
    else:
        lbaasURL = unicode(get_endpoint(k5token, "loadbalancing")) + unicode("/?LoadBalancerNames.member.1=") + unicode(lbaasName) + unicode("&Version=2014-11-01&Action=DescribeLoadBalancers")

    print lbaasURL
    token = k5token.headers['X-Subject-Token']
    try:
        response = requests.get(lbaasURL,
                                 headers={
                                     'X-Auth-Token': token, 'Content-Type': 'application/json', 'Accept': 'application/json'})
        return response
    except:
        return ("\nUnexpected error:", sys.exc_info())

def delete_load_balancer(k5token, lbaasName):
    """Summary


    Returns:
        TYPE: Description
    """
    lbaasURL = unicode(get_endpoint(k5token, "loadbalancing")) + unicode("/?LoadBalancerName=") + unicode(lbaasName) + unicode("&Version=2014-11-01&Action=DeleteLoadBalancer")

    print lbaasURL
    token = k5token.headers['X-Subject-Token']
    try:
        response = requests.get(lbaasURL,
                                 headers={
                                     'X-Auth-Token': token, 'Content-Type': 'application/json', 'Accept': 'application/json'})
        return response
    except:
        return ("\nUnexpected error:", sys.exc_info())

def list_heat_stacks(k5token):
    """Summary


    Returns:
        TYPE: Description
    """
    orchestrationURL = unicode(get_endpoint(k5token, "orchestration")) + unicode("/stacks")
    print orchestrationURL
    token = k5token.headers['X-Subject-Token']
    try:
        response = requests.get(orchestrationURL,
                                 headers={
                                     'X-Auth-Token': token, 'Content-Type': 'application/json', 'Accept': 'application/json'})
        return response
    except:
        return ("\nUnexpected error:", sys.exc_info())


# delete heat stacks - pass PURGE in as stackname to delete ALL stacks
def delete_heat_stack(k5token, stack_name):
    """Summary

    Args:
        stack_name (TYPE): Description

    Returns:
        TYPE: Description
    """
    orchestrationURL = unicode(get_endpoint(k5token, "orchestration")) + unicode("/stacks")
    print orchestrationURL
    token = k5token.headers['X-Subject-Token']
    
    try:
        stackList = list_heat_stacks(k5token).json()

        # flag to capture if all stack delete requests were sent successfully = 204 response
        stackDeleteStatus = True

        # check to see if there are any stacks
        if (len(stackList['stacks']) > 0):

            # loop thru all the stacks
            for stack in stackList['stacks']:
                # check if we're deleting ALL stacks - special stackname set to PURGE or just a single stack
                if (stack_name == "PURGE") or (stack_name == stack.get('stack_name')) :
                    # ensure the stack has completed or errored before we kill a stack mid build and cause database inconsistencies
                    # Note: some stacks tack several delete attempts before deleting successfully - heat icehouse bug???
                    if (stack.get('stack_status') == "CREATE_COMPLETE") or (stack.get('stack_status') == "CREATE_FAILED") or (stack.get('stack_status') == "DELETE_FAILED"):
                        # flag to capture if all stack delete requests were sent successfully = 204 response
                        stackDeleteStatus = False
                        print 
                        deleteOrchestrationURL =  orchestrationURL +  '/' + stack.get('stack_name') + '/' + stack.get('id')
                        print 'Stack Delete URL : ' + unicode(deleteOrchestrationURL) + '\n'
                        deleteStack = requests.delete(deleteOrchestrationURL,
                                  headers={'X-Auth-Token':token,'Content-Type': 'application/json','Accept':'application/json'})
                        if deleteStack.status_code == 204:
                            # flag to capture if all stack delete requests were sent successfully = 204 response
                            stackDeleteStatus = True
                            print "Stack Delete Request Successful"
                            print "Contract : " + unicode(contract)
                            print "Project ID : " + unicode(demoProjectAid)
                            print "Stack : " + unicode(stack)
                            print "Result : " + unicode(deleteStack)                            
                        else:
                            print "Stack Delete Failed"
                            print "Contract : " + unicode(contract)
                            print "Project ID : " + unicode(demoProjectAid)
                            print "Stack : " + unicode(stack)
                            print "Error : " + unicode(deleteStack)

        # returns True for success or False for potential debug or recall attempt required
        return stackDeleteStatus
    except:
        return ("\nUnexpected error:", sys.exc_info())

# read environment variables from GoCD Agent
adminUser = os.environ.get('OS_USERNAME')
adminPassword = os.environ.get('OS_PASSWORD')
contract = os.environ.get('OS_PROJECT_DOMAIN_NAME')
projectId = os.environ.get('OS_PROJECT_ID')
project = os.environ.get('OS_PROJECT_NAME')
region = os.environ.get('OS_REGION_NAME')
stackName = os.environ.get('OS_STACK_NAME')

# Get a project scoped token
k5token = get_scoped_token(adminUser, adminPassword, contract, projectId, region)

lbaasList = list_load_balancers(k5token, "all").json()['DescribeLoadBalancersResponse']['DescribeLoadBalancersResult']['LoadBalancerDescriptions']['member']

print len(lbaasList)

while len(lbaasList) > 0:

    for lbaas in lbaasList:
        if (lbaas.get('State') == "InService"):
            print "Deleting the following LBaaS..."
            print lbaas.get('LoadBalancerName')
            delete_load_balancer(k5token, lbaas.get('LoadBalancerName'))
        else:
            print "Waiting for LBaaS deletion to complete..."
            print lbaas.get('LoadBalancerName')
            print lbaas.get('State')
    sleep(20)
    
    lbaasList = list_load_balancers(k5token, "all").json()['DescribeLoadBalancersResponse']['DescribeLoadBalancersResult']['LoadBalancerDescriptions']['member']
            

print "All LBaaS Services Removed!!!"

count = 0


while count < 3:
    deletionStatus = delete_heat_stack(k5token, stackName)
    print "Stack Removal Status " + unicode(deletionStatus)
    sleep(60)
    count = count + 1


print "Stack Removal Status " + unicode(deletionStatus)


