from setuptools import setup


setup(
    name='smoketest',
    version='0.1',
    py_modules=['yourscript'],
    install_requires=[
        'Click',
    ],
    entry_points='''
        [console_scripts]
        broker=smoke_test.broker:cli
        client=smoke_test.client:cli
        worker=smoke_test.worker:cli
        creategraph=smoke_test.data.create_graph:cli
    ''',
)
