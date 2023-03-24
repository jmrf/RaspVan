#!/usr/bin/env bash

set -e
set -o pipefail

say() {
 echo "$@" | sed \
         -e "s/\(\(@\(red\|magenta\|yellow\|blue\|magenta\|cyan\|white\|reset\|b\|u\)\)\+\)[[]\{2\}\(.*\)[]]\{2\}/\1\4@reset/g" \
         -e "s/@red/$(tput setaf 1)/g" \
         -e "s/@green/$(tput setaf 2)/g" \
         -e "s/@yellow/$(tput setaf 3)/g" \
         -e "s/@blue/$(tput setaf 4)/g" \
         -e "s/@magenta/$(tput setaf 2)/g" \
         -e "s/@cyan/$(tput setaf 6)/g" \
         -e "s/@white/$(tput setaf 7)/g" \
         -e "s/@reset/$(tput sgr0)/g" \
         -e "s/@b/$(tput bold)/g" \
         -e "s/@u/$(tput sgr 0 1)/g"
}


# Update packages and install basics
sudo apt-get update
sudo apt-get upgrade
sudo apt-get install \
   jq \
   g++ \
   software-properties-common \
   gnupg2 pass


# Docker
say @magenta[["================ Installing Docker Engine ================"]]

# Post-installation
# As per: https://docs.docker.com/engine/install/linux-postinstall/
sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker


## Docker-compose
#say @magenta[["================ Installing Docker Compose ================"]]
#sudo curl -L "https://github.com/docker/compose/releases/download/1.27.4/docker-compose-$(uname -s)-$(uname -m)" \
#    -o /usr/local/bin/docker-compose
#sudo chmod +x /usr/local/bin/docker-compose
#docker-compose --version


# Install utilities
say @magenta[["================ Installing Utilities ================"]]

# bPyTop
say @blue[["> bpytop"]]
pip install bpytop --upgrade

# Oh-my-bash
say @blue[["> .oh-my-bash"]]
sh -c "$(curl -fsSL https://raw.github.com/ohmybash/oh-my-bash/master/tools/install.sh)"

# Oh-my-bash custom themes
say @blue[["> .oh-my-bash"]]
git clone https://github.com/josemarcosrf/oh-my-bash-custom-dir.git
yes | cp -r oh-my-bash-custom-dir/* .oh-my-bash/custom

# powerline fonts
git clone https://github.com/powerline/fonts.git fonts
cd fonts
./install.sh
