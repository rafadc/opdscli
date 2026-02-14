class Opdscli < Formula
  desc "CLI tool to interact with OPDS 1.x ebook catalogs"
  homepage "https://github.com/rafadc/opdscli"
  url "https://github.com/rafadc/opdscli/archive/refs/tags/v0.1.0.tar.gz"
  sha256 ""  # Fill in after release
  license "MIT"

  depends_on "python@3.12"
  depends_on "uv"

  def install
    system "uv", "sync", "--no-dev"
    system "uv", "run", "pyinstaller", "--noconfirm", "opdscli.spec"
    bin.install "dist/opdscli"
  end

  test do
    assert_match "0.1.0", shell_output("#{bin}/opdscli --version")
  end
end
