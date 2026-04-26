import { Box, Typography } from "@mui/material";

export default function AQIHeader() {
  return (
    <Box
      sx={{
        position: "absolute",
        top: 60,
        left: 10,
        zIndex: 9999,
        color: "#fff",
        fontFamily: "Inter, sans-serif",
      }}
    >
      {/* TITLE */}
      <Typography
        sx={{
          fontSize: 42,
          fontWeight: 800,
          lineHeight: 1.1,
          letterSpacing: "0.5px",
        }}
      >
        AIR QUALITY <br /> FORECAST
      </Typography>

      {/* SUBTITLE */}
      <Typography
        sx={{
          mt: 2,
          fontSize: 20,
          fontWeight: 800,
        }}
      >
        PM2.5 • NEXT 6 HOURS
      </Typography>

      {/* DESCRIPTION */}
      <Typography
        sx={{
          mt: 1,
          fontSize: 18,
        }}
      >
        Real-time AI-powered predictions <br />
        from sensor network
      </Typography>
    </Box>
  );
}