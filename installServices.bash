#!/bin/bash

#scan all of the files in the services directory
for file in services/*.service; do
    #get the name of the service
    service=$(basename $file .service)
    echo "Installing $service"
    #stop the service if it is running
    systemctl stop $service
    # #disable the service
    systemctl disable $service
    # #remove the service file from the systemd directory
    rm /etc/systemd/system/$service.service
    # #copy the new service file to the systemd directory
    cp $file /etc/systemd/system/
    # #enable the service
    systemctl enable $service
    # #start the service
    systemctl start $service
done
