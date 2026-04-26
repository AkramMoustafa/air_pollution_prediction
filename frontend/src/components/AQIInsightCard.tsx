import { Box, Typography } from "@mui/material";
type AQIStaticBoxProps = {
  selectedPoint: any;
  prediction: any;
  loading: boolean;
};
export default function AQIStaticBox({
  selectedPoint,
  prediction,
  loading,
}: AQIStaticBoxProps) {
const forecast = [
  { label: "1 HOUR", value: prediction?.pm25_1h ?? null },
  { label: "3 HOURS", value: prediction?.pm25_3h ?? null },
  { label: "6 HOURS", value: prediction?.pm25_6h ?? null },
  { label: "12 HOURS", value: prediction?.pm25_12h ?? null },
];

const getAQIStatus = (value: number | null) => {
  if (value == null) return { label: "No Data", color: "#9ca3af" };

  if (value <= 50) return { label: "Good", color: "#22c55e" };
  if (value <= 100) return { label: "Moderate", color: "#facc15" };
  if (value <= 150)
    return { label: "Unhealthy for Sensitive Groups", color: "#f97316" };
  if (value <= 200) return { label: "Unhealthy", color: "#ef4444" };

  return { label: "Very Unhealthy", color: "#7c3aed" };
};
const trendUp =
  prediction?.pm25_1h != null &&
  selectedPoint?.pm25 != null &&
  prediction.pm25_1h > selectedPoint.pm25;
const current = getAQIStatus(selectedPoint?.pm25 ?? null);
const trendValues = [
  selectedPoint?.pm25 ?? 0,
  prediction?.pm25_1h ?? 0,
  prediction?.pm25_3h ?? 0,
  prediction?.pm25_6h ?? 0,
  prediction?.pm25_12h ?? 0,
];
const maxVal = Math.max(...trendValues);
const minVal = Math.min(...trendValues);

const normalize = (v: number) => {
  if (maxVal === minVal) return 20;
  return 30 - ((v - minVal) / (maxVal - minVal)) * 20;
};
const path = trendValues
  .map((v, i) => {
    const x = i * 20; // spacing
    const y = normalize(v);
    return `${i === 0 ? "M" : "L"}${x} ${y}`;
  })
  .join(" ");
  return (
    <Box
      sx={{
        position: "absolute",
        bottom: 20,
        left: 20,
        width: 320,
        zIndex: 9999,

        background: "linear-gradient(180deg, #021B1E 0%, #031F23 100%)",
        borderRadius: "18px",
        p: 2,
        color: "#fff",
        boxShadow: "0 10px 40px rgba(0,0,0,0.5)",
        fontFamily: "Inter, sans-serif",
      }}
    >
      {/* TITLE */}
      <Typography sx={{ fontSize: 11, opacity: 0.6 }}>
        AIR QUALITY INDEX
      </Typography>

      {/* HEADER (FIXED STRUCTURE) */}
      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: "auto 1fr",
          alignItems: "center",
          gap: 2,
          mt: 0.5,
        }}
      >
        <Typography
          sx={{
            fontSize: 60,
            fontWeight: 700,
          color: current.color,
            lineHeight: 1,
          }}
        >
         {selectedPoint?.pm25 != null ? selectedPoint.pm25.toFixed(0) : "--"}
        </Typography>

        <Typography
          sx={{
        color: current.color,
            fontSize: 16,
            fontWeight: 500,
            lineHeight: 1.3,
          }}
        >
        {current.label.includes("for") ? (
        <>
            {current.label.split("for")[0]}
            <br />
            for {current.label.split("for")[1]}
        </>
        ) : (
        current.label
        )}
        </Typography>
      </Box>

      {/* PROGRESS */}
      <Box
        sx={{
          height: 6,
          mt: 1.5,
          mb: 2,
          background: "rgba(255,255,255,0.08)",
          borderRadius: 20,
          overflow: "hidden",
        }}
      >
        <Box
          sx={{
           width: `${Math.min((selectedPoint?.pm25 ?? 0) / 200 * 100, 100)}%`,
            height: "100%",
            background: current.color,
            color: current.color,
            borderRadius: 20,
          }}
        />
      </Box>

      {/* FORECAST */}
      <Typography sx={{ fontSize: 11, opacity: 0.6, mb: 1 }}>
        FORECAST (AQI)
      </Typography>

{forecast.map((item, i) => {
  const aqi = getAQIStatus(item.value);

  return (
    <Box
      key={i}
      sx={{
        display: "grid",
        gridTemplateColumns: "90px 10px 40px 1fr",
        alignItems: "center",
        mb: 1,
      }}
    >
      {/* LABEL */}
      <Typography sx={{ fontSize: 12, opacity: 0.7 }}>
        {item.label}
      </Typography>

      {/* DOT */}
      <Box
        sx={{
          width: 8,
          height: 8,
          borderRadius: "50%",
          background: aqi.color,
        }}
      />

      {/* VALUE */}
      <Typography
        sx={{
          fontWeight: 600,
          fontSize: 16,
          color: aqi.color,
        }}
      >
        {item.value != null ? item.value.toFixed(0) : "--"}
      </Typography>

      {/* STATUS */}
      <Typography
        sx={{
          fontSize: 12,
          color: aqi.color,
          whiteSpace: "nowrap",
        }}
      >
        {aqi.label}
      </Typography>
    </Box>
  );
})}

      {/* TREND */}
      <Box
        sx={{
          mt: 2,
          pt: 1.5,
          borderTop: "1px solid rgba(255,255,255,0.06)",
        }}
      >
        <Typography sx={{ fontSize: 11, opacity: 0.6 }}>
          TREND
        </Typography>

        <Box sx={{ display: "flex", alignItems: "center", mt: 1 }}>
          {/* REAL CURVE USING SVG */}
          <Box sx={{ width: 80, height: 40 }}>
            <svg width="80" height="40">
            <path
                    d={path}
                    stroke={current.color}
                    strokeWidth="3"
                    fill="none"
                    />
            </svg>
          </Box>

          <Typography sx={{ fontSize: 12, ml: 1 }}>
            Air quality is expected to{" "}
            <span style={{color: current.color, fontWeight: 600 }}>
          {trendUp ? "worsen" : "improve"}
            </span>
          </Typography>
        </Box>
      </Box>
    </Box>
  );
}