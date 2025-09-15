; 剪映草稿处理程序 (兼容AutoHotkey v1.x)
#NoEnv
#SingleInstance, Force
SetBatchLines, -1
SetWorkingDir, %A_ScriptDir%

; 获取程序目录下的所有子目录
folderList := ""
Loop, *.*, 2, 0 ; 只查找目录，不递归
{
    if (A_LoopFileAttrib contains D) ; 确保是目录
    {
        ; 跳过系统目录和特殊目录
        if (A_LoopFileName != "." && A_LoopFileName != "..")
        {
            folderList .= A_LoopFileName "|"
        }
    }
}

; 移除最后一个竖线
StringTrimRight, folderList, folderList, 1

if (folderList = "")
{
    MsgBox, 16, 错误, 程序目录下找不到任何子目录
    ExitApp
}

; 创建GUI让用户选择草稿目录
Gui, Add, Text,, 请选择草稿目录：
Gui, Add, ListBox, vSelectedFolder w300 h150, %folderList%
Gui, Add, Button, Default w80 gButtonOK, 确定
Gui, Add, Button, x+10 w80 gButtonCancel, 取消
Gui, Show,, 选择草稿目录
return

ButtonOK:
    Gui, Submit
    draftname := SelectedFolder
    Gosub, MainProcess
return

ButtonCancel:
    ExitApp
return

MainProcess:
    ; 检查用户选择的目录是否存在
    IfNotExist, %draftname%
    {
        MsgBox, 16, 错误, 程序目录下找不到草稿目录：%draftname%
        ExitApp
    }

    ; 获取当前用户名并构建配置文件路径
    username := A_UserName
    configPath := "C:\Users\" . username . "\AppData\Local\JianyingPro\User Data\Config\globalSetting"

    ; 检查配置文件是否存在
    IfNotExist, %configPath%
    {
        MsgBox, 16, 错误, 找不到剪映配置文件：%configPath%
        ExitApp
    }

    ; 读取配置文件内容
    FileRead, configContent, %configPath%
    If ErrorLevel
    {
        MsgBox, 16, 错误, 无法读取配置文件：%configPath%
        ExitApp
    }

    ; 查找草稿目录路径
    ; 使用正则表达式匹配 currentCustomDraftPath= 后面的路径
    FoundPos := RegExMatch(configContent, "currentCustomDraftPath=(.+)", match)
    if (FoundPos = 0)
    {
        MsgBox, 16, 错误, 在配置文件中找不到 currentCustomDraftPath 值
        ExitApp
    }
    baseDraftFolder := match1

    ; 检查程序目录下的 result_high.mp4 文件是否存在
    IfNotExist, result_high.mp4
    {
        MsgBox, 16, 错误, 程序目录下找不到 result_high.mp4 文件
        ExitApp
    }

    ; 让用户选择素材保存目录（默认建议D:\剪映素材）
    FileSelectFolder, materialFolder, D:\, 3, 请选择剪映素材保存目录
    if ErrorLevel ; 如果用户取消了选择
    {
        MsgBox, 16, 错误, 未选择素材保存目录，程序退出
        ExitApp
    }

    ; 创建用户选择的素材目录（如果不存在）
    IfNotExist, %materialFolder%
        FileCreateDir, %materialFolder%

    ; 拷贝视频文件到用户选择的素材目录
    FileCopy, result_high.mp4, %materialFolder%\, 1
    If ErrorLevel
    {
        MsgBox, 16, 错误, 无法拷贝 result_high.mp4 到 %materialFolder%
        ExitApp
    }

    ; 检查目标草稿目录是否已存在
    targetDraftPath := baseDraftFolder . "\" . draftname
    IfExist, %targetDraftPath%
    {
        ; 如果目录已存在，询问用户是否删除
        MsgBox, 36, 确认覆盖, 目标草稿目录已存在：%targetDraftPath%`n`n是否删除现有目录？`n选择"是"将删除并覆盖，选择"否"将取消操作。
        IfMsgBox, No
        {
            MsgBox, 16, 取消, 用户取消操作，程序退出
            ExitApp
        }
        
        ; 用户选择Yes，删除现有目录
        FileRemoveDir, %targetDraftPath%, 1 ; 递归删除目录
        If ErrorLevel
        {
            MsgBox, 16, 错误, 无法删除现有目录：%targetDraftPath%
            ExitApp
        }
    }

    ; 拷贝草稿目录到剪映草稿目录
    FileCopyDir, %draftname%, %targetDraftPath%, 1
    If ErrorLevel
    {
        MsgBox, 16, 错误, 无法拷贝草稿目录到：%targetDraftPath%
        ExitApp
    }

    ; 处理 draft_content.json 文件
    jsonFilePath := targetDraftPath . "\draft_content.json"
    IfNotExist, %jsonFilePath%
    {
        MsgBox, 16, 错误, 找不到 draft_content.json 文件：%jsonFilePath%
        ExitApp
    }

    ; 使用 COM 对象读取 UTF-8 编码的 JSON 文件
    ; 解决中文乱码问题
    oStream := ComObjCreate("ADODB.Stream")
    oStream.Type := 2 ; 文本类型
    oStream.Charset := "utf-8" ; 设置字符集为 UTF-8
    oStream.Open
    oStream.LoadFromFile(jsonFilePath)
    jsonContent := oStream.ReadText()
    oStream.Close

    ; 查找并替换视频路径
    ; 确保路径使用双反斜杠
    StringReplace, materialFolderEscaped, materialFolder, \, \\, All
    newVideoPath := materialFolderEscaped . "\\result_high.mp4"

    ; 修复替换逻辑 - 查找 "path":"...result_high.mp4" 模式
    ; 使用正则表达式匹配完整的路径字段
    pattern = "path":"[^"]*\\result_high\.mp4"

    ; 进行替换
    newJsonContent := RegExReplace(jsonContent, pattern, """path"":""" . newVideoPath . """")

    ; 使用 COM 对象写回 UTF-8 编码的 JSON 文件
    oStream := ComObjCreate("ADODB.Stream")
    oStream.Type := 2 ; 文本类型
    oStream.Charset := "utf-8" ; 设置字符集为 UTF-8
    oStream.Open
    oStream.WriteText(newJsonContent)
    oStream.SaveToFile(jsonFilePath, 2) ; 2 = 覆盖已存在文件
    oStream.Close

    MsgBox, 64, 完成, 草稿处理完成！`n`n草稿目录：%targetDraftPath%`n视频文件：%materialFolder%\result_high.mp4
    ExitApp