"""Engineering geometry visualization for three-element Yagi designs.

Pure geometry helpers keep Plotly views consistent and independently testable.
These are dimensional drawings, not electromagnetic predictions.
"""
import math
import plotly.graph_objects as go


def geometry_segments(design):
    """Return the boom, element rods and two feed-gap arms in meters."""
    if not design.elements or not math.isfinite(design.boom_length_m):
        raise ValueError("Invalid Yagi geometry")
    segments = [{"name": "Boom", "kind": "boom",
                 "start": (0.0, 0.0, 0.0),
                 "end": (design.boom_length_m, 0.0, 0.0)}]
    for element in design.elements:
        x, half = element.position_m, element.length_m / 2
        if not all(math.isfinite(v) for v in (x, half)) or half <= 0:
            raise ValueError("Element geometry must be finite and positive")
        if element.name == "Driven":
            gap_half = design.feed_gap_m / 2
            if not (0 < gap_half < half):
                raise ValueError("Driven-element feed gap is invalid")
            segments.extend([
                {"name": "Driven −", "kind": "driven",
                 "start": (x, -half, 0.0), "end": (x, -gap_half, 0.0)},
                {"name": "Driven +", "kind": "driven",
                 "start": (x, gap_half, 0.0), "end": (x, half, 0.0)},
            ])
        else:
            segments.append({"name": element.name, "kind": "element",
                             "start": (x, -half, 0.0),
                             "end": (x, half, 0.0)})
    return segments


def dimension_rows(design, unit="cm"):
    """Dimension labels with explicit units and consistent conversion."""
    scales = {"cm": 100.0, "in": 39.37007874015748, "mm": 1000.0}
    if unit not in scales:
        raise ValueError("Unsupported unit")
    scale = scales[unit]
    return [{"Element": e.name,
             f"Boom position ({unit})": round(e.position_m * scale, 2),
             f"Length ({unit})": round(e.length_m * scale, 2)}
            for e in design.elements]


def geometry_figure(design, view="3D", unit="cm"):
    """Plot a dimensionally faithful geometry with interactive inspection."""
    scales = {"cm": 100.0, "in": 39.37007874015748, "mm": 1000.0}
    if view not in ("3D", "Top view") or unit not in scales:
        raise ValueError("Unsupported view or unit")
    scale = scales[unit]
    colors = {"boom": "#7E9BFF", "element": "#39C6C0", "driven": "#F7B267"}
    fig = go.Figure()
    for seg in geometry_segments(design):
        x = [seg["start"][0]*scale, seg["end"][0]*scale]
        y = [seg["start"][1]*scale, seg["end"][1]*scale]
        color = colors[seg["kind"]]
        if view == "3D":
            fig.add_trace(go.Scatter3d(x=x, y=y, z=[0,0], mode="lines",
                line=dict(color=color, width=9), name=seg["name"],
                hovertemplate=f'{seg["name"]}<extra></extra>'))
        else:
            fig.add_trace(go.Scatter(x=x, y=y, mode="lines",
                line=dict(color=color, width=7), name=seg["name"],
                hovertemplate=f'{seg["name"]}<extra></extra>'))
    for element in design.elements:
        x=element.position_m*scale
        y=element.length_m*scale/2
        label=f"{element.name}: {element.length_m*scale:.2f} {unit}"
        if view == "3D":
            fig.add_trace(go.Scatter3d(x=[x], y=[y], z=[0],
                mode="markers+text", text=[label], textposition="top center",
                marker=dict(size=4,color="#E9F1F8"), showlegend=False,
                hovertemplate=label+"<extra></extra>"))
        else:
            fig.add_annotation(x=x,y=y,text=label,showarrow=True,
                arrowhead=2,ax=35,ay=-30,font=dict(size=11))
    if view == "3D":
        fig.update_layout(scene=dict(
            xaxis_title=f"Boom ({unit})", yaxis_title=f"Elements ({unit})",
            zaxis_title=f"Height ({unit})",
            aspectmode="data",
            camera=dict(eye=dict(x=1.4,y=1.4,z=1.2))),
            height=530, legend=dict(orientation="h",y=-.08))
    else:
        fig.update_layout(xaxis_title=f"Boom position ({unit})",
            yaxis_title=f"Element offset ({unit})",
            yaxis=dict(scaleanchor="x",scaleratio=1), height=490,
            legend=dict(orientation="h",y=-.22))
    fig.update_layout(title=f"3-element Yagi · {design.frequency_mhz:g} MHz",
        margin=dict(l=30,r=30,t=65,b=70))
    return fig
