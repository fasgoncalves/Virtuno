
from setuptools import setup, find_packages

setup(
    name='login2fa',
    version='6.3.0',
    packages=find_packages(),
    install_requires=[
        'nicegui',
        'mysql-connector-python',
        'bcrypt',
        'requests'
    ],
    author='Francisco Gonçalves',
    description='Sistema seguro de autenticação 2FA com logging e bloqueio configuráveis.',
)
