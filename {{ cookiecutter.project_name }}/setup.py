from setuptools import setup, find_packages


setup(name='{{cookiecutter.library_name}}',
      version='0.0.1',
      author='{{cookiecutter.author_name}}',
      author_email='{{cookiecutter.author_email}}',
      license='MIT',
      packages=find_packages('src'),
      package_dir={'': 'src'})
