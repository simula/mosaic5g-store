#!/usr/bin/env python
import logging

import connexion
from connexion.resolver import RestyResolver

logging.basicConfig(level=logging.INFO)

if __name__ == '__main__':
    app = connexion.FlaskApp(__name__)
    app.add_api('./inputs/core_adapter.yaml',
                arguments={'title': 'Core Adapter Example'},
                resolver=RestyResolver('core_api'),
                strict_validation=True)
    app.run(port=9090)
