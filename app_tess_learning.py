import os
import subprocess
import glob
import cv2

# 경로 설정
tiff_folder = "./app2/images/tiff"
output_folder = "./app2/training_output"
box_folder = "./app2/images/tiff"

# 폴더가 없으면 생성
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Tesseract 명령어 확인 함수
def check_tesseract_installed():
    try:
        subprocess.run(['tesseract', '--version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("Tesseract is installed.")
    except Exception:
        print("Error: Tesseract is not installed or not in your PATH.")
        exit(1)

# 학습 프로세스 실행
def run_command_with_error_handling(command):
    """Run a command with stdout and stderr output and handle errors gracefully."""
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print("STDOUT:", result.stdout.decode('utf-8'))
        print("STDERR:", result.stderr.decode('utf-8'))
    except subprocess.CalledProcessError as e:
        print("Error occurred while running the command:", command)
        print("STDOUT:", e.stdout.decode('utf-8') if e.stdout else 'No output')
        print("STDERR:", e.stderr.decode('utf-8') if e.stderr else 'No error message')
        raise  # Rethrow the error to propagate it if necessary

# DPI 설정 함수
def set_dpi(input_path, output_path, dpi=150):
    """Set DPI of an image to the specified value."""
    image = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)
    if image is None:
        print(f"Error: Unable to read image {input_path}")
        exit(1)

    # Write the image with the specified DPI
    success = cv2.imwrite(output_path, image, [cv2.IMWRITE_TIFF_XDPI, dpi, cv2.IMWRITE_TIFF_YDPI, dpi])
    if not success:
        print(f"Error: Unable to save image with DPI {dpi} to {output_path}")
        exit(1)
        
def check_box_file(box_path):
    """Check that the .box file is valid."""
    with open(box_path, 'r', encoding='utf-8') as f:
        for line in f:
            fields = line.strip().split()
            if len(fields) != 6:
                print(f"Invalid line format: {line.strip()}")
                return False
    return True

# Tesseract 학습 함수
def train_tesseract(tiff_path, box_path, output_name):
    # Apply DPI correction first
    fixed_dpi_tiff = os.path.join(tiff_folder, f"{output_name}.tiff")
    set_dpi(tiff_path, fixed_dpi_tiff)
    
    box_check = check_box_file(box_path)
    if not box_check:
        print(f"Error: Invalid .box file format for {box_path}")
        return

    # .tr 파일 생성
    tr_file = os.path.join(output_folder, f"{output_name}.tr")
    print(f"Creating {tr_file}")

    # 디버그 메시지: 명령 실행 전 모든 파일 경로 출력
    print("Executing Tesseract training with fixed DPI TIFF and box.train parameters...")
    print(f"Fixed DPI TIFF: {fixed_dpi_tiff}")
    print(f"Output Name: {output_name}")

    run_command_with_error_handling(["tesseract", fixed_dpi_tiff, os.path.join(output_folder, output_name), "nobatch", "box.train"])

    # unicharset 생성
    unicharset_file = os.path.join(output_folder, "unicharset")
    run_command_with_error_handling(["unicharset_extractor", box_path])

    # 학습 진행 (mftraining)
    run_command_with_error_handling(["mftraining", "-F", "font_properties", "-U", unicharset_file, "-O", os.path.join(output_folder, f"{output_name}.unicharset"), tr_file])

    # 학습 진행 (cntraining)
    run_command_with_error_handling(["cntraining", tr_file])

    # combine_tessdata를 통해 최종 .traineddata 생성
    run_command_with_error_handling(["combine_tessdata", os.path.join(output_folder, output_name)])

# 메인 함수
def main():
    check_tesseract_installed()

    # tiff 폴더의 모든 .tiff 파일 찾기
    for tiff_path in glob.glob(os.path.join(tiff_folder, "*.tiff")):
        # 파일명에서 확장자를 제거하고 box 파일 경로를 찾음
        base_name = os.path.splitext(os.path.basename(tiff_path))[0]
        box_path = os.path.join(box_folder, f"{base_name}.box")
        
        print('box_path = ', box_path)

        if not os.path.exists(box_path):
            print(f"Warning: No matching .box file found for {tiff_path}")
            continue

        print(f"Training with {tiff_path} and {box_path}")
        train_tesseract(tiff_path, box_path, base_name)

if __name__ == "__main__":
    main()
