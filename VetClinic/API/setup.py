from setuptools import setup, find_packages

setup(
    name="vetclinic_api",
    version="0.1.0",
    author="PSK Proj",
    description="VetClinic FastAPI backend",
    packages=find_packages(include=["vetclinic_api", "vetclinic_api.*"]),
    python_requires=">=3.10",
    install_requires=[
        "fastapi>=0.95.0",
        "uvicorn[standard]>=0.22.0",
        "sqlalchemy>=2.0.0",
        "pydantic>=2.0.0",
        "passlib[bcrypt]>=1.7.0",
        "python-multipart>=0.0.5"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Framework :: FastAPI",
        "License :: OSI Approved :: MIT License"
    ],
)