FROM python:3.10-alpine3.13
LABEL maintainer=""

ENV PYTHONUNBUFFERED 1

# Copier le fichier des dépendances
COPY ./requirements.txt /tmp/requirements.txt

# Copier le projet Django et le fichier .env dans le conteneur
COPY . /app

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances
RUN apk add --update --no-cache --virtual .tmp-build-deps \
    build-base musl-dev && \
    pip install --upgrade pip && \
    pip install -r /tmp/requirements.txt && \
    rm -rf /tmp && \
    apk del .tmp-build-deps && \
    adduser --disabled-password --no-create-home django-user

# Définir l'utilisateur non-root
USER django-user

# Exposer le port 8001
EXPOSE 8001

# Commande par défaut pour démarrer l'application
CMD ["python", "manage.py", "runserver", "0.0.0.0:8001"]
