#!/bin/bash

set -e

function main() {
	local remote_host="$1"

	echo "Pushing to: ${remote_host}"
	rsync -avz -e ssh --exclude=__pycache__ \
		/workspaces/ha_strava/custom_components/ha_strava/ ${remote_host}:/root/config/custom_components/ha_strava &&
		echo "Restarting home assistant on ${remote_host}" &&
		ssh "${remote_host}" 'source /etc/profile.d/homeassistant.sh >/dev/null && ha core restart' &&
		echo "Push and Restart Complete!" \
		;
}

main "$@"
