from setuptools import setup, find_packages

setup(
    name="trip",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "numpy",
        "openai",
        "click"
    ],
    entry_points={
        "console_scripts": [
            "trip = trip.cli:main"
        ]
    },
    author="Your Name",
    description="Generate trip itineraries & budgets from a CSV",
)
