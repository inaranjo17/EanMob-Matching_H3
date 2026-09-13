-- HU-45: Agregar columnas geoespaciales y de matching a la tabla trayectos
ALTER TABLE trayectos
  ADD COLUMN origin_lat          DECIMAL(10, 8)  NULL,
  ADD COLUMN origin_lng          DECIMAL(11, 8)  NULL,
  ADD COLUMN destination_lat     DECIMAL(10, 8)  NULL,
  ADD COLUMN destination_lng     DECIMAL(11, 8)  NULL,
  ADD COLUMN origin_h3           VARCHAR(20)     NULL,
  ADD COLUMN destination_h3      VARCHAR(20)     NULL,
  ADD COLUMN available_seats     INT             NOT NULL DEFAULT 1,
  ADD COLUMN cost_per_passenger  DECIMAL(10, 2)  NULL,
  ADD COLUMN status
    ENUM('open','in_progress','completed','cancelled') NOT NULL DEFAULT 'open',
  ADD COLUMN vehicle_id          INT             NULL;

CREATE INDEX idx_trayectos_origin_h3      ON trayectos(origin_h3);
CREATE INDEX idx_trayectos_destination_h3 ON trayectos(destination_h3);
CREATE INDEX idx_trayectos_status         ON trayectos(status);