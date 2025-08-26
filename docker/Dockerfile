FROM thepaeth/ckan-thai_gdc:v3.0.3

USER root

#------- install extension
COPY setup/ckanext-main ${APP_DIR}/src/
WORKDIR ${APP_DIR}/src/ckanext-main
RUN /usr/local/bin/python setup.py develop
WORKDIR ${APP_DIR}


RUN chown -R ckan-sys:ckan-sys ${PYTHON_INSTALL_DIR}

RUN chown -R ckan:ckan-sys ${APP_DIR} ${CKAN_STORAGE_PATH}

USER ckan