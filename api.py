import os
import zipfile
import tempfile
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse
import pyJianYingDraft as draft
from pyJianYingDraft import trange, ShrinkMode, ExtendMode, TextBackground, TextBorder, ExportResolution, ExportFramerate
from typing import Optional

app = FastAPI()

async def process_video(
    template_name: str,
    new_draft_name: str,
    new_video_file: UploadFile,
    new_srt_file: UploadFile,
    title: str
):
    # 创建临时目录存储文件
    with tempfile.TemporaryDirectory() as temp_dir:
        # 保存上传的视频文件
        video_path = os.path.join(temp_dir, new_video_file.filename)
        with open(video_path, "wb") as buffer:
            content = await new_video_file.read()
            buffer.write(content)
        
        # 保存上传的字幕文件
        srt_path = os.path.join(temp_dir, new_srt_file.filename)
        with open(srt_path, "wb") as buffer:
            content = await new_srt_file.read()
            buffer.write(content)
        
        # 设置草稿文件夹
        draft_folder_path = r"D:\JianyingPro Drafts"
        #os.makedirs(draft_folder_path, exist_ok=True)
        draft_folder = draft.DraftFolder(draft_folder_path)
        
        # 创建剪映草稿
        if draft_folder.has_draft(new_draft_name):
            draft_folder.remove(new_draft_name)
        

        script = draft_folder.create_draft(new_draft_name,720,1280)
        
        # 获取或创建主视频轨道
        script.add_track(draft.TrackType.video, "主视频")
        
        # 替换视频素材
        new_video = draft.VideoMaterial(video_path)
        new_video_segment = draft.VideoSegment(new_video,
                                 trange(0, new_video.duration))
        script.add_segment(
            new_video_segment,"主视频"
        )

        # 创建标题文本片段
        title_text_segment = draft.TextSegment(
            title, trange(0, new_video.duration),
            background=TextBackground(color='#FFFFFF'),
            font=draft.FontType.鸿朗体,
            style=draft.TextStyle(color=(0, 0, 0), size=10,auto_wrapping=True),
            clip_settings=draft.ClipSettings(transform_y=0.8)
        )
        
        # 添加标题轨道和片段
        script.add_track(draft.TrackType.text, "新标题")
        script.add_segment(title_text_segment, "新标题")

        max_duration = new_video.duration
        min_duration = 1

        # 创建人名文本片段
        people_text_segment = draft.TextSegment(
            text='袁佳',
            timerange=trange(min_duration, max_duration/2),
            font=draft.FontType.鸿朗体,
            border=TextBorder(),
            style=draft.TextStyle(color=(222/255, 78/255, 63/255), size=13, italic=True),
            clip_settings=draft.ClipSettings(transform_x=0.126, transform_y=-0.644)
        )
        people_text_segment.add_animation(draft.TextOutro.羽化向左擦除).add_animation(draft.TextIntro.羽化向右擦开)
        script.add_track(draft.TrackType.text, "新人名")
        script.add_segment(people_text_segment, "新人名")

        # 创建职务文本片段
        pos_text_segment = draft.TextSegment(
            text='心理咨询师',
            timerange=trange(min_duration, max_duration/2),
            font=draft.FontType.鸿朗体,
            border=TextBorder(),
            style=draft.TextStyle(size=10, italic=True),
            clip_settings=draft.ClipSettings(transform_x=0.58, transform_y=-0.646)
        )
        pos_text_segment.add_animation(draft.TextOutro.羽化向左擦除).add_animation(draft.TextIntro.羽化向右擦开)
        script.add_track(draft.TrackType.text, "新职务")
        script.add_segment(pos_text_segment, "新职务")

        # 创建字幕样式
        subtitle_seg = draft.TextSegment('', timerange=None,
            font=draft.FontType.鸿朗体,
            border=TextBorder(color=(222/255, 78/255, 63/255)),
            style=draft.TextStyle(size=9, italic=True, auto_wrapping=True),
            clip_settings=draft.ClipSettings(transform_y=-0.52)
        )
        subtitle_seg.add_effect("7127676414962240805")
        
        # 添加字幕轨道并导入字幕
        script.add_track(draft.TrackType.text, "新字幕")
        script.import_srt(srt_path=srt_path, track_name="新字幕", style_reference=subtitle_seg, clip_settings=None)

        # 保存草稿
        script.save()

        # 导出视频
        ctrl = draft.JianyingController()
        export_path = r"d:\temp\jianying"
        
        # 确保导出目录存在
        os.makedirs(export_path, exist_ok=True)
        exported_video_path = os.path.join(export_path, f"{new_draft_name}.mp4")
        if(os.path.isfile(exported_video_path)):
            os.remove(exported_video_path)

        jianying_export_path=os.path.join(r'C:\Users\Administrator\Videos', f"{new_draft_name}.mp4");
        if(os.path.isfile(jianying_export_path)):
            os.remove(jianying_export_path)
        # 导出视频
        ctrl.export_draft(new_draft_name, export_path,
                         resolution=ExportResolution.RES_720P,
                         framerate=ExportFramerate.FR_30)
        
        # 等待导出完成（可能需要根据实际情况调整等待时间）
       # await asyncio.sleep(10)
        
        # 创建zip文件
        zip_path = os.path.join(export_path, f"{new_draft_name}.zip")
        if(os.path.isfile(zip_path)):
            os.remove(zip_path)
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
            # 添加草稿目录
            draft_dir = os.path.join(draft_folder_path, new_draft_name)
            print(draft_dir)
            if os.path.exists(draft_dir):
                for root, dirs, files in os.walk(draft_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, draft_folder_path)
                        zipf.write(file_path, arcname)
            
            # 添加视频素材
            zipf.write(video_path, os.path.basename(video_path))
            print(video_path)
            # 添加导出的视频
            
            print(exported_video_path)
            if os.path.exists(exported_video_path):
                zipf.write(exported_video_path, os.path.basename(exported_video_path))
        
        return zip_path

@app.post("/create_video")
async def create_video(
    template_name: str= Form(...),
    new_draft_name: str = Form(...),
    new_video: UploadFile = File(...),
    new_srt: UploadFile = File(...),
    title: str = Form(...)
):
    # 处理视频并创建zip文件
    zip_path = await process_video(
        template_name,new_draft_name, new_video, new_srt, title
    )
    
    # 返回zip文件
    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=f"{new_draft_name}.zip"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7864)