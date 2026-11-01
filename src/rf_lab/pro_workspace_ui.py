"""Professional navigation, workflow launchers, and honest export directory."""
import streamlit as st
from rf_lab.pro_workspace import WORKFLOWS,REPORT_TOOLS,search_tools,normalize_favorites

def launch(category,tool):
    st.session_state["rf_category"]=category
    st.session_state["rf_section_"+category]=tool

def favorites():
    return normalize_favorites(st.session_state.get("rf_favorites",[]))

def toggle_favorite(category,tool):
    items=favorites()
    target=(category,tool)
    if target in items:
        items.remove(target)
    else:
        items.append(target)
    st.session_state["rf_favorites"]=normalize_favorites(items)

def sidebar_tools():
    st.markdown("**Find a tool**")
    query=st.text_input("Search workspaces",placeholder="Search by name or category…",
                        key="rf_tool_search")
    if query.strip():
        results=search_tools(query)[:12]
        if not results:
            st.caption("No matching tools.")
        for category,name in results:
            st.button(name,key="rf_search_"+category+"_"+name,
                      use_container_width=True,on_click=launch,args=(category,name))
    items=favorites()
    if items:
        st.markdown("**Pinned tools**")
        for category,name in items:
            st.button("☆ "+name,key="rf_fav_"+category+"_"+name,
                      use_container_width=True,on_click=launch,args=(category,name))

def render_workflows():
    st.caption("Guided navigation between existing tools; inputs are not automatically transferred.")
    for i,flow in enumerate(WORKFLOWS):
        with st.container(border=True):
            st.markdown("#### "+flow["name"])
            st.caption(flow["description"])
            cols=st.columns(3)
            for j,((category,tool),col) in enumerate(zip(flow["steps"],cols),start=1):
                with col:
                    st.button(str(j)+". "+tool,key=f"rf_flow_{i}_{j}",
                              use_container_width=True,on_click=launch,args=(category,tool))

def render_reports():
    st.caption("Report center · discover export tools and generate reports at their source.")
    st.info("RF Lab does not store reports in a shared server-side library. "
            "Open a tool below to generate its available export; save downloads locally.")
    for category,tool,description in REPORT_TOOLS:
        with st.container(border=True):
            left,right=st.columns([4,1])
            with left:
                st.markdown("**"+description+"**")
                st.caption(category+" · "+tool)
            with right:
                st.button("Open",key="rf_report_"+tool,use_container_width=True,
                          on_click=launch,args=(category,tool))
