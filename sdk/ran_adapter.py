#!/usr/bin/env python
import logging

import connexion
from connexion.resolver import RestyResolver

logging.basicConfig(level=logging.INFO)

if __name__ == '__main__':
    app = connexion.FlaskApp(__name__)
    app.add_api('./inputs/ran_adapter.yaml',
                arguments={'title': 'RAN Adapter Example'},
                resolver=RestyResolver('api'),
                strict_validation=True)
    app.run(port=9090)
