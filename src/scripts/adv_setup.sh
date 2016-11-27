#!/bin/bash

if (test $EUID -ne 0 ); then
	echo "Please run as root"
	exit
fi

echo ""
echo "This is the advanced setup script designed for those that are familar with Linux and Python"
echo "If you wish to use the more novice setup, please run the setup.sh in the src/script folder"
echo ""
read -p "Continue? (Y/n)? " continue_script

case $continue_script in
				[yY] )
						echo "Continuing..."
				;;
				* )
						echo "Script canceled!"
						exit
				;;
esac

apt-get update
apt-get install python-dev swig libasound2-dev memcached python-pip python-alsaaudio vlc libpulse-dev python-yaml -y
pip install -r ./requirements.txt
