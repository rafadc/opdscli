import stat

from opdscli.config import (
    AppConfig,
    AuthConfig,
    CatalogConfig,
    load_config,
    save_config,
)


class TestConfigRoundTrip:
    def test_save_and_load(self, tmp_path):
        config_path = tmp_path / "test_config.yaml"
        config = AppConfig(
            default_catalog="mylib",
            catalogs={
                "mylib": CatalogConfig(
                    url="https://example.com/opds",
                    auth=AuthConfig(type="basic", username="user", password="pass"),
                ),
                "public": CatalogConfig(url="https://public.example.com/opds"),
            },
            settings={"default_format": "epub"},
        )
        save_config(config, path=config_path)
        loaded = load_config(path=config_path)

        assert loaded.default_catalog == "mylib"
        assert "mylib" in loaded.catalogs
        assert "public" in loaded.catalogs
        assert loaded.catalogs["mylib"].url == "https://example.com/opds"
        assert loaded.catalogs["mylib"].auth is not None
        assert loaded.catalogs["mylib"].auth.type == "basic"
        assert loaded.catalogs["mylib"].auth.username == "user"
        assert loaded.catalogs["mylib"].auth.password == "pass"
        assert loaded.catalogs["public"].auth is None
        assert loaded.settings["default_format"] == "epub"

    def test_bearer_auth_roundtrip(self, tmp_path):
        config_path = tmp_path / "test_config.yaml"
        config = AppConfig(
            catalogs={
                "tokenlib": CatalogConfig(
                    url="https://token.example.com/opds",
                    auth=AuthConfig(type="bearer", token="secret123"),
                ),
            },
        )
        save_config(config, path=config_path)
        loaded = load_config(path=config_path)

        assert loaded.catalogs["tokenlib"].auth is not None
        assert loaded.catalogs["tokenlib"].auth.type == "bearer"
        assert loaded.catalogs["tokenlib"].auth.token == "secret123"


class TestMissingConfig:
    def test_returns_empty_config(self, tmp_path):
        config_path = tmp_path / "nonexistent.yaml"
        config = load_config(path=config_path)
        assert config.default_catalog is None
        assert config.catalogs == {}
        assert config.settings == {}


class TestConfigPermissions:
    def test_sets_restrictive_permissions(self, tmp_path):
        config_path = tmp_path / "test_config.yaml"
        save_config(AppConfig(), path=config_path)
        mode = config_path.stat().st_mode
        assert not (mode & stat.S_IROTH)
        assert not (mode & stat.S_IWOTH)
        assert not (mode & stat.S_IRGRP)


class TestConfigOperations:
    def test_add_catalog(self, tmp_path):
        config_path = tmp_path / "test_config.yaml"
        config = AppConfig()
        config.catalogs["test"] = CatalogConfig(url="https://test.com/opds")
        config.default_catalog = "test"
        save_config(config, path=config_path)

        loaded = load_config(path=config_path)
        assert "test" in loaded.catalogs
        assert loaded.default_catalog == "test"

    def test_remove_catalog(self, tmp_path):
        config_path = tmp_path / "test_config.yaml"
        config = AppConfig(
            default_catalog="a",
            catalogs={
                "a": CatalogConfig(url="https://a.com"),
                "b": CatalogConfig(url="https://b.com"),
            },
        )
        save_config(config, path=config_path)

        loaded = load_config(path=config_path)
        del loaded.catalogs["a"]
        loaded.default_catalog = "b"
        save_config(loaded, path=config_path)

        final = load_config(path=config_path)
        assert "a" not in final.catalogs
        assert final.default_catalog == "b"
