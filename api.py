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
    backMisc: UploadFile,
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
        draft_folder_path = r"C:\Users\Administrator\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft"
        #os.makedirs(draft_folder_path, exist_ok=True)
        draft_folder = draft.DraftFolder(draft_folder_path)
        current_work_dir = os.path.dirname(__file__)
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
            style=draft.TextStyle(color=(0, 0, 0), size=13,auto_wrapping=True),
            clip_settings=draft.ClipSettings(transform_y=0.8)
        )
        
        # 添加标题轨道和片段
        script.add_track(draft.TrackType.text, "新标题")
        script.add_segment(title_text_segment, "新标题")

        max_duration = new_video.duration #单位微秒
        min_duration = 1
        # --- 修正后的背景音乐处理逻辑 ---
        if backMisc is not None: # 再次检查 filename，确保文件被上传
            # 保存背景音乐
            backMisc_path = os.path.join(temp_dir, backMisc.filename)
            with open(backMisc_path, "wb") as buffer:
                content = await backMisc.read()
                buffer.write(content)

            # 添加背景音乐
            back_misc_material = draft.AudioMaterial(backMisc_path)
            music_duration = back_misc_material.duration # 获取音乐文件的总时长 (微秒)
            print(f"音乐长度{music_duration}")
            # 添加音频轨道
            script.add_track(draft.TrackType.audio, "背景音乐")

            # 使用一个指针 track_start_time 来跟踪在轨道上放置下一个片段的起始时间
            track_start_time = 0
            while track_start_time < max_duration:
                # 计算当前片段在轨道上的结束时间
                # 它是轨道起始时间加上音乐文件时长，但不能超过视频总时长
                print(f"track_start_time：{track_start_time}，music_duration：{music_duration}，max_duration：{max_duration}")
                track_end_time = min(track_start_time + music_duration, max_duration)
                
                print(f"track_end_time：{track_end_time}")
                # 计算源文件中需要使用的时长 (源范围的结束时间)
                # 这通常就是 track_end_time - track_start_time，因为我们是从音乐开头开始取的
                source_duration = track_end_time - track_start_time
                print(f"source_duration：{source_duration}")
                source_end_time = source_duration # 因为源范围从 0 开始

                # 创建源时间范围 (在音乐文件内部)
                source_range = trange(0, source_end_time)

                # 创建目标时间范围 (在轨道上)
                target_range = trange(track_start_time, track_end_time)

                # 创建音频片段
                segment = draft.AudioSegment(
                    back_misc_material,
                    source_timerange=source_range,
                    speed=1.0,
                    target_timerange=target_range,
                    volume=0.3
                )
                
                # 将片段添加到轨道
                script.add_segment(segment, "背景音乐")

                # 更新 track_start_time 为下一个片段的起始时间
                track_start_time = track_end_time # 关键：下一个片段从当前片段结束处开始

        # --- 背景音乐处理逻辑结束 ---

        # 创建人名文本片段
        people_text_segment = draft.TextSegment(
            text='谭博文',
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
            clip_settings=draft.ClipSettings(transform_x=0.60, transform_y=-0.646)
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
        export_path = r"c:\temp\jianying"
        
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
            zipf.write(os.path.join(current_work_dir, 'ImportJianYing.exe'), '导入剪映.exe')
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
    backMisc: Optional[UploadFile] = None,
    title: str = Form(...) 
):
    # 处理视频并创建zip文件
    zip_path = await process_video(
        template_name,new_draft_name, new_video, new_srt, backMisc,title
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