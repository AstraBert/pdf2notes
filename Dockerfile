FROM condaforge/miniforge3

WORKDIR /app/
COPY ./docker/*.py /app/
COPY ./environment.yml /app/
COPY ./shell/ /app/shell/

RUN bash /app/shell/conda_env.sh

CMD ["bash", "/app/shell/run.sh"]