FROM odoo:15.0

USER root

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    fonts-thai-tlwg \
    fonts-thai-tlwg-ttf \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

# สั่ง refresh cache ของฟอนต์
RUN fc-cache -f -v

USER odoo