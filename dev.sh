#!/usr/bin/env bash


# Variables
blue_color='\033[0;34m'  # ANSI blue color.
reset_color='\e[0m'      # ANSI default color.
venv_path='./.venv'
venv_subdir=$([[ -d /c/Windows ]] && echo 'Scripts' || echo 'bin')
venv_activator_path="${venv_path}/${venv_subdir}/activate"


#########
# Shorthand for deactivating the virtual environment.
#########
# Usage: quit
#########
quit()
{
  deactivate
  unset quit
}


# Main Entry Point
if [[ ${BASH_SOURCE-} == "$0" ]]; then
  echo -e "You must source this script: ${blue_color}source $0${reset_color}" >&2
  return 1
fi

# Create the virtual environment if it doesn't exist
if [[ ! -f $venv_activator_path ]]; then
  python -m venv $venv_path
fi

# Activate the virtual environment
source "$venv_activator_path"
pip install -e .[dev]

echo -e '\nVirtual environment activated.'
echo -e "To execute the unit tests, run ${blue_color}pytest${reset_color}"
echo -e "To exit the virtual environment, run ${blue_color}quit${reset_color}"
