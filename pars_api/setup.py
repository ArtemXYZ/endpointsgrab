# from setuptools import setup, find_packages

setup(
    name='your_library',
    version='0.1.0',
    author='Your Name',
    author_email='your_email@example.com',
    description='A brief description of your library',
    packages=find_packages(),
    install_requires=[
        # Здесь перечислите зависимости, например:
        'numpy',
        'requests',
    ],
)