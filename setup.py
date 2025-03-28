from setuptools import setup, find_packages

setup(
    name='jtop_fast_gpu_utilization_only',
    version='0.1.0',
    description='A fast GPU utilization monitoring library for NVIDIA Jetson devices, reading from sysfs at high frequency.',
    author='dav-ell',
    author_email='delliott537@gmail.com',
    url='https://github.com/dav-ell/jtop_fast_gpu_utilization_only',
    packages=find_packages(),
    install_requires=[],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: Apache 2.0 License',
        'Operating System :: POSIX :: Linux',
        'Intended Audience :: Developers',
        'Topic :: System :: Monitoring',
    ],
    python_requires='>=3.6',
)