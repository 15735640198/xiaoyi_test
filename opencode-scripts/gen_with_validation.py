#!/usr/bin/env python3
"""
opencode 脚本生成 - 校验续跑编排器

场景:
  你先用 `opencode run "生成XXX脚本"` 跑一次生成, 拿到 session_id。
  再用本脚本对已存在的 session 做「校验 -> 失败则续跑」循环,
  直到校验通过或达到最大续跑次数。

用法:
  python3 gen_with_validation.py \
      --session-id <SID> \
      --validate-cmd "python check_wlan.py" \
      [--continue-prompt "..."] \
      [--max-retry 3] \
      [--opencode-bin opencode] \
      [--workdir .] \
      [--run-arg --agent=xxx]

校验脚本约定 (--validate-cmd):
  - 退出码 0 = 通过
  - 退出码非 0 = 失败
  - stdout/stderr 末尾将作为失败明细拼进续跑 prompt 传给 opencode
"""
import argparse
import shlex
import subprocess
import sys
from pathlib import Path

DEFAULT_CONTINUE_PROMPT = (
    "请继续完成脚本生成 SKILL 中尚未完成的流程步骤, "
    "并修复下面校验发现的问题后重新生成/补全脚本:\n\n"
)

# 续跑 prompt 中拼接失败明细的最大字符数, 避免过长
MAX_DETAIL_CHARS = 2000


def run_command(args, *, cwd=None, label=""):
    """运行命令, 实时把 stdout/stderr 转发到控制台, 返回 (returncode, output).

    stderr 合并进 stdout, 保证顺序与终端一致, 同时累积全文用于后续处理。
    """
    print(f"\n{'=' * 60}")
    print(f"[{label}] 执行: {' '.join(args)}")
    print(f"{'=' * 60}")

    try:
        proc = subprocess.Popen(
            args,
            cwd=str(cwd) if cwd else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError:
        print(f"错误: 找不到可执行文件: {args[0]}", file=sys.stderr)
        return 127, f"executable not found: {args[0]}"
    except Exception as e:
        print(f"错误: 启动命令失败: {e}", file=sys.stderr)
        return 1, f"failed to start: {e}"

    out_lines = []
    try:
        assert proc.stdout is not None
        for line in proc.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            out_lines.append(line)
    finally:
        proc.wait()

    print(f"\n[{label}] 退出码: {proc.returncode}")
    return proc.returncode, "".join(out_lines)


def tail_text(text, max_chars=MAX_DETAIL_CHARS):
    """取文本末尾 max_chars 字符, 去除尾部多余空白。"""
    text = text.rstrip()
    if len(text) <= max_chars:
        return text
    return "..." + text[-max_chars:]


def validate(validate_cmd, cwd):
    """运行校验脚本, 返回 (ok: bool, detail: str)。"""
    args = shlex.split(validate_cmd, posix=(sys.platform != "win32"))
    rc, output = run_command(args, cwd=cwd, label="校验")
    return rc == 0, output


def continue_session(opencode_bin, sid, prompt, cwd, extra_run_args):
    """opencode run -s <sid> '<prompt>' 续跑已有 session。"""
    args = [opencode_bin, "run", "-s", sid]
    args.extend(extra_run_args)
    args.append(prompt)
    rc, _ = run_command(args, cwd=cwd, label="续跑 opencode")
    return rc == 0


def main():
    parser = argparse.ArgumentParser(
        description="opencode 脚本生成 - 校验续跑编排器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--session-id", required=True,
                        help="已存在的 opencode session ID")
    parser.add_argument("--validate-cmd", required=True,
                        help="校验脚本命令 (退出码 0=通过, 非 0=失败)")
    parser.add_argument("--continue-prompt", default=DEFAULT_CONTINUE_PROMPT,
                        help="续跑时给 opencode 的提示语前缀 (失败明细会拼在其后)")
    parser.add_argument("--max-retry", type=int, default=3,
                        help="最大续跑次数 (默认 3); 校验最多 max-retry+1 次")
    parser.add_argument("--opencode-bin", default="opencode",
                        help="opencode 可执行文件 (默认 opencode)")
    parser.add_argument("--workdir", default=".",
                        help="opencode/校验脚本的工作目录 (默认当前目录)")
    parser.add_argument("--run-arg", action="append", default=[],
                        help="传给 opencode run 的额外参数, 可重复, "
                             "如 --run-arg --agent=xxx --run-arg --model=yyy")
    args = parser.parse_args()

    workdir = Path(args.workdir).resolve()
    if not workdir.exists():
        print(f"错误: 工作目录不存在: {workdir}", file=sys.stderr)
        sys.exit(2)

    print("opencode 脚本生成 - 校验续跑编排器")
    print(f"  session_id  : {args.session_id}")
    print(f"  校验命令    : {args.validate_cmd}")
    print(f"  最大续跑    : {args.max_retry}")
    print(f"  工作目录    : {workdir}")
    print(f"  opencode    : {args.opencode_bin}")
    if args.run_arg:
        print(f"  额外参数    : {args.run_arg}")
    print()

    last_detail = ""
    for attempt in range(args.max_retry + 1):
        round_no = attempt + 1
        print(f"\n########## 第 {round_no} 轮校验 (共至多 {args.max_retry + 1} 轮) ##########")

        ok, output = validate(args.validate_cmd, workdir)
        last_detail = output

        if ok:
            print(f"\n✅ 校验通过 (第 {round_no} 轮), 脚本完整性 OK, 结束。")
            sys.exit(0)

        print(f"\n❌ 第 {round_no} 轮校验失败。")
        if attempt == args.max_retry:
            print(f"已达最大续跑次数 ({args.max_retry}), 不再续跑, 退出。")
            print(f"\n最后一次校验失败明细:\n{tail_text(last_detail)}")
            sys.exit(1)

        detail = tail_text(last_detail)
        full_prompt = f"{args.continue_prompt}{detail}"
        print(f"\n准备第 {attempt + 1} 次续跑 session, 提示语已附带校验明细...")
        ok2 = continue_session(
            args.opencode_bin, args.session_id, full_prompt, workdir, args.run_arg
        )
        if not ok2:
            print("⚠ 续跑命令本身异常退出, 仍会进入下一轮校验确认磁盘产物。")

    # 理论上不会走到这里
    sys.exit(1)


if __name__ == "__main__":
    main()
