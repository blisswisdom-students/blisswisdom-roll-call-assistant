# 福智學員平臺點名助手

![screenshot](assets/screenshot.png)


https://user-images.githubusercontent.com/1842626/230267365-0a8bd99a-c63b-4779-85f9-568493657e92.mp4


* [Development](#development)
  + [Environment](#environment)
    - [Reference](#reference)
  + [Setup](#setup)
  + [Packaging](#packaging)
    - [Desktop application](#desktop-application)
  + [Design concepts](#design-concepts)
* [License](#license)

## Usage

### Prerequisites

1. [Firefox Browser](https://www.mozilla.org/en-US/firefox/browsers/)

## Development

### Environment

1. [Python](https://www.python.org/) 3.10
2. [Poetry](https://python-poetry.org/)
3. [PyCharm](https://www.jetbrains.com/pycharm/)
4. [Git](https://git-scm.com/)

#### Reference

[My Python Development Environment, 2020 Edition](https://jacobian.org/2019/nov/11/python-environment-2020/)

### Setup

```
poetry install
poetry run pip install numpy --upgrade
```

### Packaging

#### Desktop application

```
poetry run pyinstaller --clean desktop.spec
```

### Design concepts

1. [Object-oriented programming](https://en.wikipedia.org/wiki/Object-oriented_programming) (OOP)
2. [Model–view–viewmodel](https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93viewmodel) (MVVM)

### Key libraries

1. [Qt for Python](https://www.qt.io/qt-for-python)
2. [Selenium](https://www.selenium.dev/)
3. [EasyOCR](https://github.com/JaidedAI/EasyOCR)

## License

[Mozilla Public License Version 2.0](https://www.mozilla.org/en-US/MPL/2.0/)
