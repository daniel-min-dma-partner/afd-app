# syntax=docker/dockerfile:1
FROM openjdk:slim
COPY --from=python:3 / /

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /code/
COPY . /code/

# Install pip requirements
RUN pip install -r requirements.txt

# Expose port
EXPOSE 8000

# Sets the system call signal used to stop the instance
STOPSIGNAL SIGTERM

# Run entrypoint
RUN chmod a+x /code/docker-entrypoint.sh
ENTRYPOINT [ "sh", "docker-entrypoint.sh" ]
