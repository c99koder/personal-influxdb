## Dockerfile
You can obviously customize this however you want, and likely will.   I wrote this quick and dirty to extract all the parameters I needed for the librelinkup and config python files to work.  You can add/delete as necessary.

Breaking the file down:

`FROM python:3.11.4-alpine3.18`
###### this  defines the base image to use.  I wanted to keep things nice and tidy, so I used the python 3.11 image based on alpine 3.18.  you can use whatever you want.

`LABEL maintainer="Evan Richardson (evanrich81[at]gmail.com)"`
###### **The maintainer of the image.  I posted this to dockerhub, so I stuck my name and email on there, please don't spam me.  You can change to whatever you want.**

`WORKDIR /app`
###### This sets the working directory for the container to `/app`

`COPY requirements.txt /app/` 
###### Self explanitory.

`RUN pip install --no-cache-dir -r requirements.txt`
###### Installs the requirements, leaving no cache behind (smaller final image)

    COPY librelinkup.py /
    COPY config.py /
###### These lines copy the python files to the root directory (could go in app if you wanted).  These could also be consolidated on one line for one less layer, but not the end of the world.
 

    ENV INFLUXDB_HOST="default_host"
    ENV INFLUXDB_PORT="default_port"
    ENV INFLUXDB_USER="default_username" 
    ENV INFLUXDB_PASSWORD="default_password"
    ENV LIBRELINKUP_DATABASE="database"
    ENV LIBRELINKUP_USERNAME="librelinkup_username" 
    ENV LIBRELINKUP_PASSWORD="librelinkup_password"
##### This block of env variables defines env variables that will be available to the container.  Set these to whatever you want.

`CMD ["python", "/librelinkup.py"]`
##### And finally, the run line.  This runs the selected python file upon start of the container.


## Running the container
If you use the cronjob in the kubernetes folder, it will add the environmental variables automatically.  if not, then you should run this image in a way similar to:
`docker run -e VAR1=VALUE1 -e VAR2=VALUE  evanrich/libre2influx:latest`