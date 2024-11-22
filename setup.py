from setuptools import setup

package_name = 'user_input_package'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/config', ['user_input_package/embeddings.yaml']),
    ],
    install_requires=['setuptools', 'PyYAML'],
    zip_safe=True,
    maintainer='Your Name',
    maintainer_email='your_email@example.com',
    description='User input package for ROS',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'ui_node = user_input_package.UI:main',
            'nlp_call = user_input_package.NLP_call:main',
            'port_to_bt = user_input_package.portToBT:main',
        ],
    },
)
