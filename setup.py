from setuptools import setup, find_packages

setup(
    name="wedding-photo-upload",
    version="2.0.0",
    description="A beautiful wedding photo sharing application",
    author="Wedding Photo Upload",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "flask>=3.0.0,<4.0.0",
        "pillow>=10.0.0,<11.0.0",
        "qrcode[pil]>=7.4.0,<8.0.0",
        "werkzeug>=3.0.0,<4.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "flake8>=6.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.5.0",
            "pytest-flask>=1.2.0",
            "pytest-mock>=3.11.0",
        ],
        "prod": [
            "gunicorn>=21.0.0,<22.0.0",
        ]
    },
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "wedding-photos=run:main",
        ],
    },
)