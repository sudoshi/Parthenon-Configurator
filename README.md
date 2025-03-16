# Parthenon Configurator

Parthenon Configurator is a tool designed to simplify the configuration and deployment of the Ohdsi/Broadsea stack. This project streamlines the setup process, ensuring a smooth and efficient deployment of OHDSI (Observational Health Data Sciences and Informatics) tools plus ancillary tools like Authentik and Portainer, as well as other dockerized tools for medical informatics data profiling, transformation, and visualization.

## Features

- Easy configuration of Broadsea services
- Support for multiple environments
- Automated generation of configuration files
- Integration with Docker for deployment
- Simplified management of OHDSI tools

## Prerequisites

Before using Broadsea Configurator, ensure you have the following installed:

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)
- [Git](https://git-scm.com/downloads)
- [PostgreSQL](https://www.postgresql.org/download/) (if using a local database)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/sudoshi/Broadsea-Configurator.git
   cd Broadsea-Configurator
   ```
2. Configure environment variables by copying the example file:
   ```bash
   cp .env.example .env
   ```
3. Modify `.env` with your desired settings.
4. Run the setup script (if available) or manually configure as needed.

## Usage

### Running Broadsea Configurator

To generate the required configuration files and deploy Broadsea, use:

```bash
./configure.sh
```

or manually execute the required setup steps as described in the documentation.

### Deploying with Docker

If using Docker, start the services with:

```bash
docker-compose up -d
```

Check running services:
```bash
docker ps
```

## Configuration

The configuration is managed through environment variables in the `.env` file. Below are some key parameters:

- `DB_HOST` – Database host (default: `localhost`)
- `DB_PORT` – Database port (default: `5432`)
- `DB_USER` – Database username
- `DB_PASSWORD` – Database password
- `OHDSI_WEBAPI_URL` – WebAPI service URL

For a full list of configurable parameters, check `.env.example`.

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -m "Add new feature"`
4. Push to the branch: `git push origin feature-name`
5. Open a Pull Request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For questions or support, open an issue on GitHub or reach out to the project maintainers.

