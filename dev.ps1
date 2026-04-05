
# Variables
$blue_color = "$([char]0x1B)[0;34m"  # ANSI blue color
$reset_color = "$([char]0x1B)[0m"    # ANSI reset color
$venv_path = "./.venv"
$venv_subdir = if (Test-Path 'C:/Windows') { 'Scripts' } else { 'bin' }
$venv_activator_path = "$venv_path/$venv_subdir/Activate.ps1"


#########
# Shorthand for deactivating the virtual environment.
#########
# Usage: quit
#########
function quit
{
    deactivate
    Remove-Item Function:quit
}


# Main Entry Point
# Create the virtual environment if it doesn't exist.
if (-not (Test-Path $venv_activator_path))
{
    python -m venv $venv_path
}

# Activate the virtual environment
. $venv_activator_path

# Install dependencies
pip install -e .[dev]
Remove-Item -Path .\tortoise_embedding.egg-info -Recurse -Force

Write-Host "`nVirtual environment activated."
Write-Host "To execute the unit tests, run ${blue_color}pytest${reset_color}"
Write-Host "To exit the virtual environment, run ${blue_color}quit${reset_color}"
