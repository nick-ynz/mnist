# MNIST 
## This is a Docker application that can receive users' image with a handwritten digit and predict that digit.  
## To run this application, follow the steps below:  
>1.Make sure the latest Docker is installed, if not installed, click [here](https://docs.docker.com/install/) to do the installaion.  
2.There are two ways to get the application:  
(1)Use `git clone` to get the application, and open the folder 'build_predict_1' in the terminal, then run `docker build --tag=[image_name] .`   
(2)Or you can run `docker pull nickynz/mnist` in the terminal.  
3.run `docker pull cassandra`  
4.After building the image, you will be able to use `docker images` command to see the built image.    
5.Finally, you can run these images:   
```bash
docker run --name some-cassandra -p 9042:9042 -d cassandra:latest
docker run -d -p [port]:80 [image_name]
```
>The port is the local port that you want to have access to, and the image_name is the one you use in step 3 or `nickynz/mnist`  
>6.Use `curl` to transfer image to the application.
```bash
curl -F "file=@/path/to/your/image/1.jpg" http://0.0.0.0:[port]/mnist
```
>Use the port in step 5. 
>If everything is properly configured, you will be able to see the following result:
```bash
Upload File Name: [file name]
Upload Time: [time]
Prediction: [The predicted digit]
```  
## If you have any issues, make sure to check the log file in the container and paste it on the issue.
## How to check the log file:
>1.Get into the container using the following command:
```bash
docker exec -it [container] /bin/bash
```
>The container can either be the container ID or the container name. Both of them are shown in the `docker ps` command.  
>2.The flask log file is in /app/flask.log, and the cassandra log files are in /var/log/cassandra, open the file using `more` and you will be able to find the error.
## This project is supported by Dr.Zhang. I'd like to express my gratitude to him for helping us with this project.
