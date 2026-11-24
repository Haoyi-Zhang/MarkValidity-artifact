#!/usr/bin/env python3
"""Plot received comparison traces and their first stopping certificates.

The independent own-order trace is required; no fallback trajectory is invented.
The matched-disclosure trace remains bound in the receipt and tables but is not
repeated in the main figure, whose comparison is shared evidence versus the
fair independently scheduled baseline.
"""
from __future__ import annotations

import argparse
import csv
from fractions import Fraction
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator
import numpy as np


def read_csv(path):
    with gzip.open(path, "rt") as stream:
        return list(csv.DictReader(stream))


def first_certificate(lower, upper, steps):
    for lo, hi, step in zip(lower, upper, steps):
        if lo > 0 or hi < 0 or lo == hi == 0:
            return int(step)
    return None


def from_rows(rows, lower, upper):
    steps = np.asarray([int(row["step"]) for row in rows])
    lows = np.asarray([int(row[lower]) for row in rows])
    highs = np.asarray([int(row[upper]) for row in rows])
    assert len(steps) and steps[0] == 0 and np.all(np.diff(steps) == 1)
    assert np.all(lows <= highs)
    return dict(steps=steps, lower=lows, upper=highs,
                first=first_certificate(lows, highs, steps))


def _style_from_output(out: Path):
    module_path = Path(out).parent / "figure_style.py"
    if module_path.is_file():
        spec = importlib.util.spec_from_file_location("markvalidity_figure_style", module_path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module
    class Fallback:
        INK="#202A33"; BLUE="#0072B2"; ORANGE="#D55E00"; GRAY="#59636D"
        MID_GRAY="#8A949D"; LIGHT_GRAY="#E8ECEF"; PALE_BLUE="#E6F2F7"; GRID="#CBD2D8"
        @staticmethod
        def apply_style(base_size=9.0):
            plt.rcParams.update({"font.family":"serif","font.serif":["Nimbus Roman","Liberation Serif","DejaVu Serif"],
                "font.size":base_size,"mathtext.fontset":"stix","pdf.fonttype":42,
                "ps.fonttype":42,"svg.fonttype":"none","axes.spines.top":False,
                "axes.spines.right":False})
        @staticmethod
        def save_vector_bundle(fig,out,title,dpi=240):
            out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
            fig.savefig(out,metadata={"Title":title,"CreationDate":None,"ModDate":None})
            fig.savefig(out.with_suffix(".svg"),metadata={"Title":title,"Date":None})
            fig.savefig(out.with_suffix(".png"),dpi=dpi)
    return Fallback


def draw_joint_comparisons(cases, out, config=None):
    """Draw actual width traces and a direct first-certificate cost strip."""
    cfg={"height":3.35,"line_width":1.55,"certificate_height":0.78,
         "legend_y":0.995,"x_padding":0.065,"show_savings":True}
    if config: cfg.update(config)
    style=_style_from_output(Path(out));style.apply_style(9.0)
    blue,gray,grid=style.BLUE,style.GRAY,style.GRID
    fig=plt.figure(figsize=(5.95,float(cfg["height"])))
    gs=fig.add_gridspec(2,2,height_ratios=[3.4,float(cfg["certificate_height"])],
                        left=.095,right=.985,bottom=.165,top=.800,wspace=.30,hspace=.07)
    trace_axes=[];cost_axes=[]
    method_styles=[("Shared obligation",blue,"-",float(cfg["line_width"])),
                   ("Separate scores / own order",gray,"--",float(cfg["line_width"])-.05)]
    handles=[Line2D([0],[0],color=c,ls=ls,lw=lw) for _,c,ls,lw in method_styles]
    fig.legend(handles,[m[0] for m in method_styles],loc="upper center",
               bbox_to_anchor=(.54,.985),ncol=2,frameon=False,
               handlelength=2.8,columnspacing=1.6)
    records=[]
    for col,case in enumerate(cases):
        denominator=case["denominator"]
        shown=case["series"][:2]
        firsts=[int(s["first"]) for s in shown]
        x_max=max(firsts)*(1+float(cfg["x_padding"]))
        ax=fig.add_subplot(gs[0,col]);trace_axes.append(ax)
        for series,(_,color,ls,lw) in zip(shown,method_styles):
            first=int(series["first"])
            mask=series["steps"]<=first
            x=series["steps"][mask]
            widths=100*(series["upper"][mask]-series["lower"][mask])/denominator
            ax.step(x,widths,where="post",color=color,ls=ls,lw=lw,zorder=3)
            y=float(widths[-1])
            ax.plot([first],[y],marker="o",markersize=4.4,markerfacecolor="white",
                    markeredgewidth=1.1,markeredgecolor=color,zorder=4)
            # Put the annotation inside the panel and route it to the actual point.
            if col==1 and first==1:
                xytext=(.26,.74);coords="axes fraction";ha="left"
            elif color==blue:
                xytext=(.43,.77);coords="axes fraction";ha="left"
            else:
                xytext=(.94,.36);coords="axes fraction";ha="right"
            ax.annotate(f"q = {first:,}",xy=(first,y),xycoords="data",
                        xytext=xytext,textcoords=coords,ha=ha,va="center",
                        color=color,fontsize=8.6,fontweight="bold",
                        arrowprops=dict(arrowstyle="-",lw=.75,color=color,
                                        shrinkA=2,shrinkB=3))
        title=("HumanEval\nStock − S1" if col==0 else "Sanitized MBPP\nStock − S4")
        ax.set_title(title,pad=6,fontweight="bold")
        ax.set_xlim(0,x_max);ax.set_ylim(bottom=0)
        ax.set_ylabel("Joint-gap width (pp)" if col==0 else "")
        ax.grid(axis="y",color=grid,lw=.55,alpha=.8)
        ax.tick_params(axis="x",labelbottom=False,length=0)
        ax.yaxis.set_major_locator(MaxNLocator(nbins=4))
        ax.text(-.18,1.08,"("+chr(97+col)+")",transform=ax.transAxes,
                fontweight="bold",fontsize=9.2)

        bx=fig.add_subplot(gs[1,col],sharex=ax);cost_axes.append(bx)
        bx.set_ylim(-.5,1.5);bx.set_yticks([1,0],["Shared","Separate"])
        bx.set_xlabel("")
        for y,(first,(_,color,ls,lw)) in enumerate(zip(firsts,method_styles)):
            yy=1-y
            bx.hlines(yy,0,first,color=color,linestyle=ls,linewidth=lw)
            bx.plot([first],[yy],marker="o",markersize=4.2,color=color)
            offset=max(x_max*.018,4)
            x_text=min(first+offset,x_max*.98)
            bx.text(x_text,yy,f"{first:,}",va="center",
                    ha="left" if x_text>first else "right",fontsize=8.4,color=color)
        if cfg["show_savings"]:
            saved=firsts[1]-firsts[0]
            bx.text(.98,.95,f"{saved:,} fewer",transform=bx.transAxes,
                    ha="right",va="top",fontsize=8.0,color=blue)
        bx.spines["left"].set_visible(False);bx.spines["right"].set_visible(False)
        bx.spines["top"].set_visible(False)
        bx.tick_params(axis="y",length=0,pad=4,labelsize=8.0)
        bx.xaxis.set_major_locator(MaxNLocator(nbins=5,integer=True))
        records.append({"title":case["title"],"denominator":denominator,
                        "shown_first_certificates":firsts,
                        "matched_order_first_certificate":int(case["series"][2]["first"])})
    fig.supxlabel("Additional candidate suites after reference-identity admission", y=.025, fontsize=9.0)
    style.save_vector_bundle(fig,Path(out),"Joint comparison traces and first certificates")
    plt.close(fig)
    return records


def draw_conditional_comparisons(cases,out):
    """Legacy renderer retained for the staged generator; later replaced by the paired figure."""
    style=_style_from_output(Path(out));style.apply_style(9.0)
    fig,axes=plt.subplots(2,2,figsize=(5.95,3.7),layout="constrained")
    for row,case in enumerate(cases):
        for y,side,label,color in [(1,"left","Stock",style.GRAY),(0,"right",case["right_label"],style.BLUE)]:
            lo,hi=case[side+"_interval"];axes[row,0].plot([lo,hi],[y,y],color=color,lw=2.3)
        lo,hi=case["margin"];axes[row,1].axvline(0,color=style.GRAY,ls="--",lw=.8)
        axes[row,1].plot([lo,hi],[0,0],color=style.BLUE,lw=2.3)
    style.save_vector_bundle(fig,Path(out),"Conditional comparison placeholder")
    plt.close(fig)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--conditional-out",type=Path)
    parser.add_argument("--analysis",type=Path)
    parser.add_argument("--comparison-costs",type=Path)
    args=parser.parse_args()
    old=args.analysis or args.artifact/"results/revision-sew-natural/analysis-primary"
    new=(args.comparison_costs or args.artifact/"results/revision-sew-comparison-costs")/"retrospective-primary"
    bindings={}
    def bind_input(path):
        bindings[Path(os.path.relpath(path,args.artifact)).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
    comparisons=json.loads((old/"comparisons.json").read_text())
    cases=[];conditional_cases=[]
    for case,title in [("humaneval__stock__s1","HumanEval: stock − S1"),
                       ("mbpp__stock__s4","MBPP: stock − S4")]:
        series=[]
        for method in ["coupled","independent"]:
            path=new/"traces"/f"{case}__{method}__J.csv.gz"
            series.append(from_rows(read_csv(path),"lower","upper"));bind_input(path)
        path=old/"traces"/f"{case}__joint_width_per_suite.csv.gz"
        series.append(from_rows(read_csv(path),"independent_J_lower","independent_J_upper"));bind_input(path)
        cases.append(dict(title=title,denominator=comparisons[case]["denominator"],series=series))
        cert=comparisons[case]["schedules"]["conditional_differences_first"]["first_certificates"]["coupled_C"]
        snapshot=cert["snapshot"]
        conditional_cases.append(dict(title=title,right_label="S1" if case.startswith("humaneval") else "S4",
            queries=cert["suite_queries"],
            left_interval=[float(Fraction(snapshot["left_C"][e])) for e in ["lower","upper"]],
            right_interval=[float(Fraction(snapshot["right_C"][e])) for e in ["lower","upper"]],
            margin=[snapshot["coupled_C"][e] for e in ["lower","upper"]]))
    records=draw_joint_comparisons(cases,args.out)
    if args.conditional_out:draw_conditional_comparisons(conditional_cases,args.conditional_out)
    bind_input(old/"comparisons.json")
    receipt={"status":"GENERATED_FROM_RECEIVED_TRACES","input_sha256":bindings,
             "depicted_methods":["Shared obligation","Separate scores / own order"],
             "matched_order_retained_in_tables_and_receipt":True,
             "cases":records,
             "first_certificates":[{case["title"]:[int(s["first"]) for s in case["series"]]} for case in cases],
             "legend_order":["Shared obligation","Separate scores / own order"],
             "scope":"Real saved trajectories shown only through each method's first certificate; the cost strips share the same x-scale as the trajectories."}
    args.out.with_suffix(".json").write_text(json.dumps(receipt,indent=2)+"\n")


if __name__=="__main__":main()
