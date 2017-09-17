#!/bin/sh
set -e
set -o pipefail

if [ -z ${NEWUSER+x} ]; then
	echo 'WARN: No user was defined, defaulting to root.'
	echo 'WARN: failsafe will save files as root:root.'
	echo '      To prevent this, start the container with -e NEWUSER=$USER'
    failsafe
else
	# The root user already exists, so we only need to do something if
	# a user has been specified.
	adduser -s /bin/sh -D $NEWUSER
	su $NEWUSER -c "failsafe $@"
fi
