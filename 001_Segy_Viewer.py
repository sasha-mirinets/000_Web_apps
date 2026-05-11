import streamlit as st
import segyio
import numpy as np
import matplotlib.pyplot as plt
import tempfile
import os

st.set_page_config(layout="wide")

st.title("SEG-Y Viewer")

uploaded_file = st.file_uploader(
    "Ciao! Please upload your sgy file",
    type=["sgy", "segy"]
)

if uploaded_file is not None:

    with tempfile.NamedTemporaryFile(delete=False, suffix=".sgy") as tmp_file:
        tmp_file.write(uploaded_file.read())
        temp_path = tmp_file.name

    filename = os.path.basename(uploaded_file.name).split('.')[0]

    with segyio.open(temp_path, "r", ignore_geometry=True) as sbp:

        data = segyio.tools.collect(sbp.trace[:])

        traceno = np.array(sbp.attributes(segyio.TraceField.FieldRecord))
        traceno_min = np.min(traceno)
        traceno_max = np.max(traceno)
        
#        chan = np.array(sbp.attributes(segyio.TraceField.TraceNumber))        

        sou_x = np.array(sbp.attributes(segyio.TraceField.SourceX))
        sou_y = np.array(sbp.attributes(segyio.TraceField.SourceY))
        scalar = np.array(sbp.attributes(segyio.TraceField.SourceGroupScalar))
        scalar[scalar == 0] = 1
        scale_factor = np.where(scalar < 0,1.0 / abs(scalar), scalar)
        sou_x = sou_x * scale_factor
        sou_y = sou_y * scale_factor
        idx_min = np.argmin(traceno)
        idx_max = np.argmax(traceno)
        sou_x1 = sou_x[idx_min]
        sou_y1 = sou_y[idx_min]
        sou_x2 = sou_x[idx_max]
        sou_y2 = sou_y[idx_max]

        trace_header_1 = sbp.header[0]

        dt_ms = (trace_header_1[segyio.TraceField.TRACE_SAMPLE_INTERVAL] * 0.001)
        nt = trace_header_1[segyio.TraceField.TRACE_SAMPLE_COUNT]
        t_ms = np.arange(0, nt * dt_ms, dt_ms)
        t_max = np.max(t_ms)

        st.sidebar.header("Display Settings")

#        channel = st.sidebar.slider(
#            "Сhan",
#           int(np.min(chan)),
#            int(np.max(chan)),
#            int(np.min(chan))
#        )

        time_down = st.sidebar.slider(
            "time_down (ms)",
            0,
            int(t_max),
            int(t_max)
        )

        time_up = st.sidebar.slider(
            "time_up (ms)",
            0,
            int(t_max),
            min(0, int(t_max))
        )

        TRACENO_Left = st.sidebar.slider(
            "TRACENO_Left",
            0,
            data.shape[0] - 1,
            0
        )

        TRACENO_Right = st.sidebar.slider(
            "TRACENO_Right",
            1,
            data.shape[0],
            data.shape[0]
        )

        vmin = st.sidebar.slider(
            "Amplitude min",
            -5000,
            0,
            -500
        )

        vmax = st.sidebar.slider(
            "Amplitude max",
            0,
            5000,
            500
        )

        cmap = st.sidebar.selectbox(
            "Colormap",
            ["gray_r", "gray", "seismic", "seismic_r", "RdGy", "RdGy_r"],
            index=0
        )

        display_data = data[TRACENO_Left:TRACENO_Right, :]

        st.subheader("File Information")

        col1, col2 = st.columns(2)

        with col1:
            st.write(f"Filename: {filename}")
            st.write(f"Trace min: {traceno_min}")
            st.write(f"Trace max: {traceno_max}")
            st.write(f"Sample interval (ms): {dt_ms}")

        with col2:
            st.write(f"Trace length (ms): {t_max}")
            st.write(f"Start X: {sou_x1:.2f}")
            st.write(f"Start Y: {sou_y1:.2f}")
            st.write(f"End X: {sou_x2:.2f}")
            st.write(f"End Y: {sou_y2:.2f}")

        st.subheader("Screen Display")

        fig, ax = plt.subplots(figsize=(14, 8))

        im = ax.imshow(
            display_data.T,
            cmap=cmap,
            norm=plt.Normalize(vmin=vmin, vmax=vmax),
            aspect='auto',
            extent=[
                TRACENO_Left,
                TRACENO_Right,
                t_max,
                0
            ]
        )

        ax.set_title(f"Time section, Line {filename}")

        ax.set_xlabel("Trace number")
        ax.set_ylabel("Time (ms)")

        ax.set_ylim([time_down, time_up])

        plt.colorbar(im, ax=ax, label="Amplitude")

        st.pyplot(fig)

    os.remove(temp_path)