#!/usr/bin/python3
import os.path
import logger
import argparse
import boto3
import time as time
import subprocess
import os


def parse_args():
  """Parse arguments"""

  parser = argparse.ArgumentParser(description='Create a Jenkins server on AWS')
  parser.add_argument('--keyfile', required=True,
                      help='The keyfile to connect to the instance.')
  parser.add_argument('--account', required=True,
                      help='The AWS account to use.')
  return parser.parse_args()


def run_command(cmd):
  """Runs a command using subprocesses"""

  (status, output) = subprocess.getstatusoutput(cmd)
  if status == 0:
    logger.console('\tComplete!')
  else:
    logger.console('Error: ' + str(status) + '. Check log for details')
  logger.log(output)


def get_resource(account):
  """Creates a resource to EC2. Returns the resource"""
  session = boto3.Session(profile_name=account, region_name='eu-west-1')
  return session.resource('ec2')


def create_security_group(ec2):
  """Checks if the security group (httpssh) exists given a connection.
  Creates it if it does not exist.
  """

  logger.console('Checking for security group: httpssh')

  groups = ec2.meta.client.describe_security_groups(Filters=[{'Name': 'group-name', 'Values': ['httpssh']}])['SecurityGroups']
  if len(groups) == 0:
    security_group = ec2.create_security_group(GroupName='httpssh', Description='Only HTTP and SSH')

    ip_ranges = [{'CidrIp': '0.0.0.0/0'}]
    ip_v6_ranges = [{'CidrIpv6': '::/0'}]
    permissions = [{
        'IpProtocol': 'TCP',
        'FromPort': 80,
        'ToPort': 80,
        'IpRanges': ip_ranges,
        'Ipv6Ranges': ip_v6_ranges
    }, {
        'IpProtocol': 'TCP',
        'FromPort': 443,
        'ToPort': 443,
        'IpRanges': ip_ranges,
        'Ipv6Ranges': ip_v6_ranges
    }, {
        'IpProtocol': 'TCP',
        'FromPort': 22,
        'ToPort': 22,
        'IpRanges': ip_ranges,
        'Ipv6Ranges': ip_v6_ranges
    }]
    security_group.authorize_ingress(IpPermissions=permissions)
    logger.console('Created security group: httpssh')

  else:
    logger.console('Found Security Group: httpssh')


def create_instance(ec2, ami, keyfile):
  """Creates an instance on Amazon Linux given a connection.
  Returns the instance.
  """

  logger.console('Creating instance')

  instances = ec2.create_instances(
    ImageId=ami,
    InstanceType='t2.micro',
    KeyName=keyfile[:-4].split('/')[-1],
    MaxCount=1,
    MinCount=1,
    SecurityGroups=['httpssh'],
    TagSpecifications=[
      {
        'ResourceType': 'instance',
        'Tags': [
          {
            'Key': 'name',
            'Value': 'jenkins-server'
          },
        ]
      },
    ])

  # Only one instance create so just return the one
  return instances[0]


def install_jenkins(ip, keyfile):
  """ Install Jenkins on an instance given it's ip address and key"""

  copy_install_script_cmd = "scp -i " + keyfile + " ./install-jenkins.sh ubuntu@" + ip + ":."
  logger.console("Copying installation script to server")
  run_command(copy_install_script_cmd)

  grant_permission_cmd = "ssh -t -i " + keyfile + " ubuntu@" + ip + " 'chmod +x ./install-jenkins.sh'"
  logger.console("Granting execute permissions to installtion script")
  run_command(grant_permission_cmd)

  run_script_cmd = "ssh -t -i " + keyfile + " ubuntu@" + ip + " 'sudo ./install-jenkins.sh'"
  logger.console("Installing Jenkins")
  run_command(run_script_cmd)


def main():
  """Main function for script"""

  args = parse_args()
  keyfile = args.keyfile
  account = args.account

  logger.createLog(os.path.basename(__file__)[:-3])

  # Connect to EC2, create SecGroup if needed, start an instance
  ec2_resource = get_resource(account)
  logger.console('Connected to EC2')

  ami = 'ami-785db401'  # Ubuntu
  # ami = 'ami-acd005d5'  # Amazon Linux

  create_security_group(ec2_resource)
  instance = create_instance(ec2_resource, ami, keyfile)

  # Wait for some time before connecting to  instance via SSH
  logger.console('Waiting for instance to boot')
  instance.wait_until_running()
  logger.console('Running')

  instance.load()
  logger.console('Public ip address received: ' + str(instance.public_ip_address))

  logger.console('Updating instance')
  run_command("ssh -t -o StrictHostKeyChecking=no -i " + keyfile + " ubuntu@" + str(instance.public_ip_address) + " 'sudo apt -y update'")

  # Install Jenkins
  #install_jenkins(str(instance.public_ip_address), keyfile)


# This is the standard boilerplate that calls the main() function.

if __name__ == '__main__':
  main()
