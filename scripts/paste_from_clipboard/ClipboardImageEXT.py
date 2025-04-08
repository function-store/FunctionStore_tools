"""
Extension for TouchDesigner that allows pasting images from the clipboard
directly into the network, similar to Figma's paste functionality.

Features:
- Paste image from clipboard with a single click
- Position image at mouse location
- Options to save as TOP or component
- Automatically uses image's native resolution
"""
from TDStoreTools import StorageManager
import TDFunctions as TDF
import os
import time
import uuid
import sys
import numpy as np
from dot_chat_util import DotChatUtil

class ClipboardImageEXT(DotChatUtil):
    """
    ClipboardImageEXT allows pasting images from clipboard directly into TouchDesigner networks.
    
    Features:
    - Paste image from clipboard
    - Position at mouse location
    - Options for TOP or component
    """
    def __init__(self, ownerComp):
        # Initialize parent class first
        super().__init__(ownerComp)
        
        # Setup logger
        self.logger = self.ownerComp.op('Logger').ext.Logger
        self.logger.log('ClipboardImageEXT initialized', 'INFO')
        # Add a flag to prevent double execution
        self._is_pasting = False
        # Setup parameters
        self.setup_parameters()
        
        # Check platform compatibility
        self.is_windows = sys.platform == 'win32'
        if not self.is_windows:
            self.logger.log("This extension is currently Windows-only", 'WARNING')
        
        # Initialize ctypes and Windows constants
        if self.is_windows:
            self._init_clipboard_ctypes()
        self.ownerComp.par.Imagewidth = 0
        self.ownerComp.par.Imageheight = 0
        self.ownerComp.op('Logger').par.Clearlog.pulse()
        # self.ownerComp.par.Status = "Ready"

        # popMenu
        self.popMenu = self.ownerComp.op('popMenu')
        self.PopMenuItemsShortcuts = {'File In':'1', 'ScriptTOP':'2','Annotate':'3','Cancel':'esc'}


    def _init_clipboard_ctypes(self):
        """Initialize ctypes and Windows constants for clipboard access"""
        import ctypes
        from ctypes import wintypes
        
        # Store these as class attributes for reuse
        self.ctypes = ctypes
        self.wintypes = wintypes
        
        # Define Windows constants
        self.CF_BITMAP = 2
        self.CF_DIB = 8
        self.CF_DIBV5 = 17
        
        # Define bitmap header structure
        class BITMAPINFOHEADER(ctypes.Structure):
            _fields_ = [
                ("biSize", wintypes.DWORD),
                ("biWidth", wintypes.LONG),
                ("biHeight", wintypes.LONG),
                ("biPlanes", wintypes.WORD),
                ("biBitCount", wintypes.WORD),
                ("biCompression", wintypes.DWORD),
                ("biSizeImage", wintypes.DWORD),
                ("biXPelsPerMeter", wintypes.LONG),
                ("biYPelsPerMeter", wintypes.LONG),
                ("biClrUsed", wintypes.DWORD),
                ("biClrImportant", wintypes.DWORD),
            ]
        self.BITMAPINFOHEADER = BITMAPINFOHEADER
        
        # Define RGB quad for color table
        class RGBQUAD(ctypes.Structure):
            _fields_ = [
                ("rgbBlue", ctypes.c_ubyte),
                ("rgbGreen", ctypes.c_ubyte),
                ("rgbRed", ctypes.c_ubyte),
                ("rgbReserved", ctypes.c_ubyte),
            ]
        self.RGBQUAD = RGBQUAD
        
        # Get Windows DLLs
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32
        
        # Define function prototypes
        self.OpenClipboard = self.user32.OpenClipboard
        self.OpenClipboard.argtypes = [wintypes.HWND]
        self.OpenClipboard.restype = wintypes.BOOL
        
        self.CloseClipboard = self.user32.CloseClipboard
        self.CloseClipboard.restype = wintypes.BOOL
        
        self.EnumClipboardFormats = self.user32.EnumClipboardFormats
        self.EnumClipboardFormats.argtypes = [wintypes.UINT]
        self.EnumClipboardFormats.restype = wintypes.UINT
        
        self.GetClipboardData = self.user32.GetClipboardData
        self.GetClipboardData.argtypes = [wintypes.UINT]
        self.GetClipboardData.restype = wintypes.HANDLE
        
        self.GlobalLock = self.kernel32.GlobalLock
        self.GlobalLock.argtypes = [wintypes.HGLOBAL]
        self.GlobalLock.restype = wintypes.LPVOID
        
        self.GlobalUnlock = self.kernel32.GlobalUnlock
        self.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
        self.GlobalUnlock.restype = wintypes.BOOL
        
        self.GlobalSize = self.kernel32.GlobalSize
        self.GlobalSize.argtypes = [wintypes.HGLOBAL]
        self.GlobalSize.restype = ctypes.c_size_t
    
    def get_last_error_message(self):
        """Get detailed Windows error message"""
        error_code = self.ctypes.GetLastError()
        if error_code == 0:
            return "No error"
        
        FORMAT_MESSAGE_FROM_SYSTEM = 0x00001000
        FORMAT_MESSAGE_IGNORE_INSERTS = 0x00000200
        
        buffer_size = 256
        buffer = self.ctypes.create_unicode_buffer(buffer_size)
        
        self.kernel32.FormatMessageW(
            FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_IGNORE_INSERTS,
            None,
            error_code,
            0,
            buffer,
            buffer_size,
            None
        )
        
        return f"Error {error_code}: {buffer.value.strip()}"
    
    def setup_parameters(self):
        """Setup the extension parameters."""
        # Core Actions - paste options
        self.create_parameter('Pasteimage', 'pulse', 'Settings', 
                            label='Paste Image',
                            section=True,
                            help_text='Paste image from clipboard as TOP')
        
        self.create_parameter('Pastescriptop', 'pulse', 'Settings',
                            label='Paste As ScriptOP',
                            help_text='Paste image from clipboard as a scriptTOP')
        
        self.create_parameter('Pasteannotate', 'pulse', 'Settings',
                            label='Paste As Note',
                            help_text='Paste image from clipboard as an annotate component')
        
        # Settings
        self.create_parameter('Folderpath', 'str', 'Settings',
                            section=True,
                            label='Save Folder',
                            default='clipboard_images',
                            help_text='Folder to save images')
        
        self.create_parameter('Positionatmouse', 'bool', 'Settings',
                            label='Position at Mouse',
                            default=True,
                            help_text='Position image at current mouse location')
        
        # Status indicators
        self.create_parameter('Status', 'str', 'Settings',
                            section=True,
                            label='Status',
                            default='Ready')
        
        self.create_parameter('Imagewidth', 'int', 'Settings',
                            label='Image Width',
                            default=0,
                            help_text='Width of last pasted image')
        
        self.create_parameter('Imageheight', 'int', 'Settings',
                            label='Image Height',
                            default=0,
                            help_text='Height of last pasted image')
    
    def Pasteimage(self):
        if self.ownerComp.par.Bypass.eval():
            return
        """Paste image from clipboard as TOP"""
        self.logger.log("[ClipboardImageEXT] Starting Pasteimage", 'INFO')
        self.paste_image('top')
        
    def Pastescriptop(self):
        if self.ownerComp.par.Bypass.eval():
            return
        """Paste image from clipboard as a scriptTOP"""
        self.paste_image('scriptop')
        
    def Pasteannotate(self):
        if self.ownerComp.par.Bypass.eval():
            return
        """Paste image from clipboard as an annotate component"""
        self.paste_image('annotate')
        
    def paste_image(self, save_type):
        """Main method to paste image from clipboard"""
        try:
            # Prevent double execution
            if hasattr(self, '_is_pasting') and self._is_pasting:
                self.logger.log("[ClipboardImageEXT] Already processing a paste operation, skipping", 'INFO')
                return
                
            self._is_pasting = True
            self.logger.log(f"[ClipboardImageEXT] Starting paste_image with save_type: {save_type}", 'INFO')
            # self.ownerComp.par.Status = "Getting clipboard image..."
            
            # Check platform compatibility
            if not self.is_windows:
                self.logger.log("This extension is currently Windows-only", 'ERROR')
                # self.ownerComp.par.Status = "Error: Windows-only feature"
                self._is_pasting = False
                return
            
            # Get image from clipboard (now returns numpy array)
            image_array = self.get_clipboard_image()
            if image_array is None:
                self.logger.log("No image found in clipboard", 'WARNING')
                # self.ownerComp.par.Status = "No image in clipboard"
                self._is_pasting = False
                return
            
            # Update image dimensions in status
            height, width = image_array.shape[:2]  # numpy is height, width ordering
            self.ownerComp.par.Imagewidth = width
            self.ownerComp.par.Imageheight = height
            self.logger.log(f"[ClipboardImageEXT] Image found with dimensions: {width}x{height}", 'INFO')
            
            # Process based on save type
            if save_type == 'top':
                # Create TOP with image saved to disk
                self.logger.log("[ClipboardImageEXT] Creating TOP from saved image", 'INFO')
                self.create_top_from_image(image_array)
            
            elif save_type == 'scriptop':
                # Create scriptTOP with image data
                self.logger.log("[ClipboardImageEXT] Creating scriptTOP with image", 'INFO')
                self.create_script_top_from_image(image_array)
            
            elif save_type == 'annotate':
                # Create annotateCOMP with image
                self.logger.log("[ClipboardImageEXT] Creating annotateCOMP with image", 'INFO')
                self.create_annotate_comp_with_image(image_array)
            
            # self.ownerComp.par.Status = f"Image pasted successfully ({width}x{height})"
            self.logger.log(f"[ClipboardImageEXT] Image pasted successfully ({width}x{height})", 'INFO')
            
        except Exception as e:
            self.logger.log(f"Error pasting image: {str(e)}", 'ERROR')
            # self.ownerComp.par.Status = f"Error: {str(e)}"
        
        finally:
            # Reset the flag when done
            self._is_pasting = False
            
    def get_clipboard_image(self):
        """
        Get image from clipboard using ctypes
        Returns a numpy array with RGBA data
        """
        # Check if we're on Windows
        if not self.is_windows:
            self.logger.log("Cannot get clipboard image: Windows-only feature", 'WARNING')
            return None
        
        try:
            self.logger.log("[ClipboardImageEXT] Getting image from clipboard using ctypes", 'INFO')
            
            # Open clipboard
            if not self.OpenClipboard(None):
                self.logger.log(f"Failed to open clipboard: {self.get_last_error_message()}", 'WARNING')
                return None
            
            try:
                # Check available formats for debugging
                self.logger.log("[ClipboardImageEXT] Available clipboard formats:", 'INFO')
                format_id = self.EnumClipboardFormats(0)
                while format_id:
                    format_name = None
                    if format_id == self.CF_BITMAP:
                        format_name = "CF_BITMAP"
                    elif format_id == self.CF_DIB:
                        format_name = "CF_DIB"
                    elif format_id == self.CF_DIBV5:
                        format_name = "CF_DIBV5"
                        
                    if format_name:
                        self.logger.log(f"[ClipboardImageEXT] Format ID: {format_id} ({format_name})", 'INFO')
                    else:
                        self.logger.log(f"[ClipboardImageEXT] Format ID: {format_id}", 'INFO')
                    format_id = self.EnumClipboardFormats(format_id)
                
                # Check for DIB format first (preferred)
                h_dib = self.GetClipboardData(self.CF_DIB)
                if h_dib and h_dib != 0:
                    h_dib_uint = self.ctypes.c_void_p(h_dib).value
                    self.logger.log(f"[ClipboardImageEXT] DIB data found: handle 0x{h_dib_uint:X}", 'INFO')
                    return self._process_dib_handle(h_dib)
                
                # Check for DIBV5 format if DIB not available
                h_dibv5 = self.GetClipboardData(self.CF_DIBV5)
                if h_dibv5 and h_dibv5 != 0:
                    h_dibv5_uint = self.ctypes.c_void_p(h_dibv5).value
                    self.logger.log(f"[ClipboardImageEXT] DIBV5 data found: handle 0x{h_dibv5_uint:X}", 'INFO')
                    return self._process_dib_handle(h_dibv5)
                
                self.logger.log("[ClipboardImageEXT] No image data found in clipboard", 'INFO')
                return None
                
            finally:
                # Always close clipboard
                self.CloseClipboard()
                
        except Exception as e:
            self.logger.log(f"Error getting clipboard image: {str(e)}", 'ERROR')
            
            # Ensure clipboard is closed
            try:
                self.CloseClipboard()
            except:
                pass
                
            return None
    
    def has_clipboard_image(self):
        """
        Quickly check if there's an image in the clipboard without processing it
        Returns True if an image is found, False otherwise
        """
        # Check if we're on Windows
        if not self.is_windows:
            return False
        
        try:
            # Open clipboard
            if not self.OpenClipboard(None):
                return False
            
            try:
                # Only check for the presence of supported formats
                # Check for DIB format first (preferred)
                h_dib = self.GetClipboardData(self.CF_DIB)
                if h_dib and h_dib != 0:
                    return True
                
                # Check for DIBV5 format if DIB not available
                h_dibv5 = self.GetClipboardData(self.CF_DIBV5)
                if h_dibv5 and h_dibv5 != 0:
                    return True
                
                # Check for bitmap format as last resort
                h_bitmap = self.GetClipboardData(self.CF_BITMAP)
                if h_bitmap and h_bitmap != 0:
                    return True
                
                return False
                
            finally:
                # Always close clipboard
                self.CloseClipboard()
                
        except Exception:
            # Ensure clipboard is closed
            try:
                self.CloseClipboard()
            except:
                pass
                
            return False
    
    def _process_dib_handle(self, h_dib):
        """Process DIB handle and convert to numpy array without PIL"""
        try:
            import numpy as np
        except ImportError:
            self.logger.log("numpy is required but not available", 'ERROR')
            return None
        
        # Lock the memory
        data_ptr = self.GlobalLock(h_dib)
        if not data_ptr:
            error_info = self.get_last_error_message()
            self.logger.log(f"Failed to lock DIB data: {error_info}", 'ERROR')
            return None
        
        try:
            # Get the BITMAPINFOHEADER
            header = self.ctypes.cast(data_ptr, self.ctypes.POINTER(self.BITMAPINFOHEADER)).contents
            
            # Verify header size
            if header.biSize < self.ctypes.sizeof(self.BITMAPINFOHEADER):
                self.logger.log(f"Invalid DIB header size: {header.biSize}", 'ERROR')
                return None
            
            # Get image dimensions and color depth
            width = header.biWidth
            height = abs(header.biHeight)  # Height can be negative for top-down DIBs
            bit_count = header.biBitCount
            is_top_down = header.biHeight < 0
            
            self.logger.log(f"[ClipboardImageEXT] Image info: {width}x{height}, {bit_count} bits per pixel", 'INFO')
            self.logger.log(f"[ClipboardImageEXT] Image orientation: {'top-down' if is_top_down else 'bottom-up'}", 'INFO')
            
            # Calculate color table size
            clr_used = header.biClrUsed
            if clr_used == 0 and bit_count < 16:
                clr_used = 1 << bit_count
            
            # Calculate offsets
            palette_size = clr_used * self.ctypes.sizeof(self.RGBQUAD)
            bits_offset = header.biSize + palette_size
            
            # For BI_BITFIELDS compression (type 3), we have three additional DWORDs
            if header.biCompression == 3 and bit_count >= 16:
                bits_offset += 12  # 3 DWORDs (4 bytes each)
            
            # Get the image data directly using ctypes and pointer arithmetic
            header_ptr = self.ctypes.cast(data_ptr, self.ctypes.c_void_p)
            bits_ptr = self.ctypes.c_void_p(header_ptr.value + bits_offset)
            
            # Calculate bytes per row (with padding to DWORD boundary)
            bytes_per_pixel = bit_count // 8
            if bit_count < 8:
                bytes_per_pixel = 1
                    
            row_size = ((width * bit_count + 31) // 32) * 4
            image_size = row_size * height
            
            # Get total data size
            data_size = self.GlobalSize(h_dib)
            
            # Safety check for buffer overrun
            if bits_offset + image_size > data_size:
                image_size = data_size - bits_offset
                if image_size <= 0:
                    self.logger.log("Invalid image size calculation", 'ERROR')
                    return None
            
            # Direct approach for 32-bit BGRA
            if bit_count == 32:
                # Create a ctypes array for the image data
                pixel_type = self.ctypes.c_ubyte * image_size
                pixel_array = pixel_type()
                
                # Copy the data from the DIB to our buffer
                self.ctypes.memmove(pixel_array, bits_ptr, image_size)
                
                # Convert to numpy array
                array = np.frombuffer(pixel_array, dtype=np.uint8).reshape((height, width, 4))
                
                # Convert BGRA to RGBA using numpy
                rgba = array[:, :, [2, 1, 0, 3]].copy()  # Important: create a contiguous copy!
                
                # Note: When using ctypes directly, we don't need to flip the image
                # This would only be necessary if using PIL's ImageGrab
                # if not is_top_down:
                #     rgba = np.flip(rgba, 0).copy()
                
                # Ensure the array is contiguous and has the right stride for TouchDesigner
                rgba = np.ascontiguousarray(rgba, dtype=np.uint8)
                
                # Return the numpy array directly
                return rgba
                
            elif bit_count == 24:
                # Create a ctypes array for the image data
                pixel_type = self.ctypes.c_ubyte * image_size
                pixel_array = pixel_type()
                
                # Copy the data from the DIB to our buffer
                self.ctypes.memmove(pixel_array, bits_ptr, image_size)
                
                # Create a numpy array for the RGB data (we'll handle padding)
                array = np.zeros((height, width, 3), dtype=np.uint8)
                
                # Extract the image data handling row padding
                for y in range(height):
                    for x in range(width):
                        row_offset = y * row_size
                        pixel_offset = row_offset + x * 3
                        if pixel_offset + 2 < image_size:
                            array[y, x, 0] = pixel_array[pixel_offset]     # Blue
                            array[y, x, 1] = pixel_array[pixel_offset + 1] # Green
                            array[y, x, 2] = pixel_array[pixel_offset + 2] # Red
                    
                # Note: When using ctypes directly, we don't need to flip the image
                # This would only be necessary if using PIL's ImageGrab
                # if not is_top_down:
                #     array = np.flip(array, 0)
                
                # Convert BGR to RGB
                rgb = array[:, :, [2, 1, 0]]
                
                # Create a fresh contiguous RGBA array with correct stride
                rgba = np.zeros((height, width, 4), dtype=np.uint8)
                rgba[:, :, 0:3] = rgb
                rgba[:, :, 3] = 255  # Full opacity
                
                # Ensure the array is contiguous
                rgba = np.ascontiguousarray(rgba, dtype=np.uint8)
                
                # Return the numpy array
                return rgba
                
            else:
                # For unsupported bit depths, return error
                self.logger.log(f"Unsupported bit depth: {bit_count}", 'ERROR')
                self.logger.log(f"[ClipboardImageEXT] Unsupported bit depth: {bit_count}", 'ERROR')
                return None
                    
        except Exception as e:
            self.logger.log(f"Error processing DIB data: {str(e)}", 'ERROR')
            import traceback
            traceback.self.logger.log_exc()  # This will help with debugging
            return None
            
        finally:
            # Always unlock the memory
            self.GlobalUnlock(h_dib)
            
    def save_image_to_disk(self, image_array):
        """Save numpy array to disk using a dedicated scriptTOP within the component"""
        try:
            # Get folder path
            folder_path = self.ownerComp.par.Folderpath.eval()
            if not folder_path:
                folder_path = 'clipboard_images'
            
            # Create folder if it doesn't exist
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            
            # Generate unique filename
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            filename = f"clipboard_{timestamp}_{unique_id}.png"
            file_path = os.path.join(folder_path, filename)
            
            # Use the dedicated scriptTOP for saving
            save_top = self.ownerComp.op('script_save')
            quiet_place = op('/sys/quiet')
            if not quiet_place.op('script_save'):
                save_top = quiet_place.copy(save_top)
            else:
                save_top = quiet_place.op('script_save')
            
            if not save_top:
                self.logger.log("Missing required 'script_save' scriptTOP in component", 'ERROR')
                raise RuntimeError("Missing required 'script_save' scriptTOP in component")
            
            if not save_top.lock:
                self.logger.log("The 'script_save' scriptTOP must be locked", 'ERROR')
                raise RuntimeError("The 'script_save' scriptTOP must be locked")
            
            # Ensure the array is contiguous with the correct memory layout
            contiguous_array = np.ascontiguousarray(image_array, dtype=np.uint8)
            
            # Copy numpy array to the scriptTOP
            save_top.copyNumpyArray(contiguous_array)
            
            # Save the image using TouchDesigner's built-in save method
            save_top.save(file_path, createFolders=True)
            
            self.logger.log(f"Image saved to: {file_path}", 'INFO')
            
            return file_path
            
        except Exception as e:
            self.logger.log(f"Error saving to disk: {str(e)}", 'ERROR')
            raise
            
    def create_top_from_image(self, image_array):
        """Create a Movie File In TOP with the clipboard image"""
        try:
            self.logger.log("[ClipboardImageEXT] Starting create_top_from_image", 'INFO')
            
            # Save image to disk first using our dedicated scriptTOP
            file_path = self.save_image_to_disk(image_array)
            
            # Determine the current network to paste into
            target_network = self.get_current_network()
            self.logger.log(f"[ClipboardImageEXT] Target network for paste: {target_network.path}", 'INFO')
            
            # Create movie file in TOP
            movie_top_name = 'clipboard_image'
            
            # Create a new movie file in TOP with a unique name
            self.logger.log(f"[ClipboardImageEXT] Creating movie TOP: {movie_top_name} with file: {file_path}", 'INFO')
            movie_top = target_network.create(moviefileinTOP, movie_top_name)
            self.logger.log(f"[ClipboardImageEXT] Created movie TOP: {movie_top.path}", 'INFO')
            
            # Set the file path AND viewer to True
            movie_top.par.file = file_path
            movie_top.viewer = True
            
            # Store reference to the created TOP
            self.clipboard_top = movie_top
            self.logger.log(f"[ClipboardImageEXT] Successfully configured movie TOP: {movie_top.path}", 'INFO')
            
            # Position at mouse immediately
            if self.ownerComp.par.Positionatmouse.eval():
                self.logger.log("[ClipboardImageEXT] Immediately positioning at mouse", 'INFO')
                self.position_at_mouse()
            
            return movie_top
            
        except Exception as e:
            self.logger.log(f"Error creating movie TOP: {str(e)}", 'ERROR')
            raise
            
    def create_script_top_with_image(self, image_array, name='clipboard_image', target_network=None):
        """
        Create a scriptTOP with the clipboard image data
        Returns the created scriptTOP
        """
        try:
            # Get image dimensions
            height, width = image_array.shape[:2]
            self.logger.log(f"[ClipboardImageEXT] Creating scriptTOP with image dimensions: {width}x{height}", 'INFO')
            
            # Ensure contiguous array with correct memory layout
            contiguous_array = np.ascontiguousarray(image_array, dtype=np.uint8)
            
            # Use provided target network or get current network
            if target_network is None:
                target_network = self.get_current_network()
            self.logger.log(f"[ClipboardImageEXT] Target network for scriptTOP: {target_network.path}", 'INFO')
            
            # Create a new scriptTOP directly in the target network
            new_top = target_network.create('scriptTOP', name)
            self.logger.log(f"[ClipboardImageEXT] Created scriptTOP: {new_top.path}", 'INFO')
            
            # Lock the scriptTOP and set viewer to True
            new_top.lock = True
            new_top.viewer = True
            
            # Remove the callbacks DAT to avoid errors
            callbacks_dat = target_network.op(f'{new_top.name}_callbacks')
            if callbacks_dat:
                self.logger.log(f"[ClipboardImageEXT] Removing callbacks DAT: {callbacks_dat.path}", 'INFO')
                callbacks_dat.destroy()
            
            # Load the numpy array directly into the scriptTOP
            new_top.copyNumpyArray(contiguous_array)
            self.logger.log(f"[ClipboardImageEXT] Loaded image data into scriptTOP: {width}x{height}", 'INFO')
            
            return new_top
            
        except Exception as e:
            self.logger.log(f"Error creating scriptTOP: {str(e)}", 'ERROR')
            raise

    def create_script_top_from_image(self, image_array):
        """Create a scriptTOP with the clipboard image data"""
        try:
            # Create the scriptTOP using the shared function
            new_top = self.create_script_top_with_image(image_array)
            
            # Store reference to created TOP
            self.clipboard_top = new_top
            
            # Position at mouse if enabled
            if self.ownerComp.par.Positionatmouse.eval():
                self.logger.log("[ClipboardImageEXT] Immediately positioning at mouse", 'INFO')
                self.position_at_mouse()
            
            self.logger.log("[ClipboardImageEXT] Successfully created scriptTOP from image", 'INFO')
            
            return new_top
            
        except Exception as e:
            self.logger.log(f"Error in create_script_top_from_image: {str(e)}", 'ERROR')
            raise

    def create_annotate_comp_with_image(self, image_array):
        """Create an annotateCOMP with the clipboard image"""
        try:
            self.logger.log("[ClipboardImageEXT] Starting create_annotate_comp_with_image", 'INFO')
            
            # Get image dimensions from numpy array (height, width)
            height, width = image_array.shape[:2]
            self.logger.log(f"[ClipboardImageEXT] Image dimensions: {width}x{height}", 'INFO')
            
            # Determine the current network to paste into
            target_network = self.get_current_network()
            
            # Create annotateCOMP
            annotate_comp = target_network.create('annotateCOMP', 'clipboard_note')
            self.logger.log(f"[ClipboardImageEXT] Created annotateCOMP: {annotate_comp.path}", 'INFO')
            
            # Create scriptTOP using the shared function
            script_top = self.create_script_top_with_image(
                image_array, 
                name='__clipboard_image', 
                target_network=target_network
            )
            
            # Setup annotateCOMP parameters
            annotate_comp.lock = True
            annotate_comp.par.Opviewerdisplay = True  # Show image
            annotate_comp.par.Opviewerfillbodytitle = True
            annotate_comp.par.Titleheight = 10  # Hide title almost completely, to be able to move it
            annotate_comp.par.Titletext = ''
            annotate_comp.par.Opviewer = script_top.name  # Set image to scriptTOP
            annotate_comp.par.Backcoloralpha = 0  # Transparent background
            
            # Set the node size to match the image dimensions
            # Add a small margin to ensure the entire image is visible
            margin = 10
            annotate_comp.nodeWidth = width + margin
            annotate_comp.nodeHeight = height + margin
            self.logger.log(f"[ClipboardImageEXT] Set annotateCOMP size to: {annotate_comp.nodeWidth}x{annotate_comp.nodeHeight}", 'INFO')
            
            # Store reference to created components
            self.clipboard_top = annotate_comp
            
            # Position at mouse if enabled
            if self.ownerComp.par.Positionatmouse.eval():
                self.logger.log("[ClipboardImageEXT] Immediately positioning at mouse", 'INFO')
                self.position_at_mouse()
                
            # Now dock the scriptTOP and hide it
            script_top.dock = annotate_comp
            script_top.showDocked = False
            script_top.expose = False
            
            self.logger.log("[ClipboardImageEXT] Successfully created annotateCOMP with image", 'INFO')
            
            return annotate_comp
            
        except Exception as e:
            self.logger.log(f"Error creating annotateCOMP: {str(e)}", 'ERROR')
            raise

    def position_at_mouse(self):
        """Position the created TOP at the current mouse position"""
        self.logger.log("[ClipboardImageEXT] Starting position_at_mouse", 'INFO')
        
        if not hasattr(self, 'clipboard_top'):
            self.logger.log("No clipboard image TOP to position", 'WARNING')
            return
        
        try:
            # Safety check to ensure the TOP still exists
            if not self.clipboard_top.valid:
                self.logger.log("[ClipboardImageEXT] TOP reference is no longer valid", 'WARNING')
                return
                
            # Use the ViewportMonitorExt directly
            self.logger.log("[ClipboardImageEXT] Using ViewportMonitorExt for positioning", 'INFO')
            mouse_data = self.ownerComp.ext.ViewportMonitorExt.UpdateMouseData()
            
            if mouse_data:
                self.logger.log(f"[ClipboardImageEXT] Mouse data: {mouse_data}", 'INFO')
                
                # Get base coordinates
                node_x = int(mouse_data['network_x'])
                node_y = int(mouse_data['network_y'])
                original_x = node_x
                original_y = node_y
                
                # Check operator type for proper offsets
                op_type = self.clipboard_top.type
                self.logger.log(f"[ClipboardImageEXT] Operator type is: {op_type}", 'INFO')
                
                # Special positioning for annotate to center it at mouse position
                if op_type == "annotate":
                    self.logger.log("[ClipboardImageEXT] Found annotate component, attempting to center", 'INFO')
                    
                    # Get the scriptTOP that contains the image
                    script_top_name = self.clipboard_top.par.Opviewer.eval()
                    script_top = self.clipboard_top.parent().op(script_top_name)
                    
                    if script_top and script_top.valid:
                        # Get actual image dimensions from the scriptTOP
                        img_width = script_top.width
                        img_height = script_top.height
                        
                        # Calculate center offsets based on actual image size
                        offset_x = int(img_width / 2)*0
                        offset_y = int(img_height / 2)*0
                        
                        # Calculate new positions
                        node_x = original_x - offset_x
                        node_y = original_y - offset_y
                        
                        self.logger.log(f"[ClipboardImageEXT] Actual image dimensions from scriptTOP: {img_width}x{img_height}", 'INFO')
                        self.logger.log(f"[ClipboardImageEXT] Calculated center offsets: x={offset_x}, y={offset_y}", 'INFO')
                        self.logger.log(f"[ClipboardImageEXT] Original mouse position: {original_x}, {original_y}", 'INFO')
                        self.logger.log(f"[ClipboardImageEXT] New annotate position after centering: {node_x}, {node_y}", 'INFO')
                        
                        # Position both the annotate and its scriptTOP
                        self.clipboard_top.nodeX = node_x
                        self.clipboard_top.nodeY = node_y
                        
                        # Move the scriptTOP with it (before docking)
                        script_top.nodeX = node_x
                        script_top.nodeY = node_y - script_top.height - 10
                        self.logger.log(f"[ClipboardImageEXT] Positioning docked scriptTOP at: {script_top.nodeX}, {script_top.nodeY}", 'INFO')
                
                # Apply specific offsets by operator type
                elif "moviefilein" in op_type:
                    offset_x = 28
                    offset_y = 86
                    node_x = original_x - offset_x
                    node_y = original_y - offset_y
                    self.logger.log(f"[ClipboardImageEXT] Positioning moviefilein with offsets: x={offset_x}, y={offset_y}")
                    self.logger.log(f"[ClipboardImageEXT] Original position: {original_x}, {original_y}")
                    self.logger.log(f"[ClipboardImageEXT] New position after offset: {node_x}, {node_y}")
                    self.clipboard_top.nodeX = node_x
                    self.clipboard_top.nodeY = node_y
                
                elif "script" in op_type:
                    offset_x = 28
                    offset_y = 86
                    node_x = original_x - offset_x
                    node_y = original_y - offset_y
                    self.logger.log(f"[ClipboardImageEXT] Positioning scriptTOP with offsets: x={offset_x}, y={offset_y}")
                    self.logger.log(f"[ClipboardImageEXT] Original position: {original_x}, {original_y}")
                    self.logger.log(f"[ClipboardImageEXT] New position after offset: {node_x}, {node_y}")
                    self.clipboard_top.nodeX = node_x
                    self.clipboard_top.nodeY = node_y
                
                self.logger.log(f"Positioned {op_type} at mouse coordinates with offset: {node_x}, {node_y}", 'INFO')
            else:
                self.logger.log("[ClipboardImageEXT] No mouse data available from ViewportMonitorExt")
                self.logger.log("No mouse data available", 'WARNING')
                
        except Exception as e:
            self.logger.log(f"Error positioning at mouse: {str(e)}", 'ERROR')
            self.logger.log(f"[ClipboardImageEXT] Error positioning at mouse: {str(e)}")

    def get_current_network(self):
        """Determine the currently active network"""
        try:
            # Try to get the current pane
            pane = ui.panes.current
            
            # Check if it's a network editor
            if pane and pane.type == PaneType.NETWORKEDITOR:
                # Get the component that the pane is looking at
                target_network = pane.owner
                if target_network:
                    self.logger.log(f"[ClipboardImageEXT] Found current network: {target_network.path}")
                    return target_network
    
            self.logger.log("[ClipboardImageEXT] Could not determine current network, using parent")
            # Fallback to parent
            return self.ownerComp.parent()
        
        except Exception as e:
            self.logger.log(f"Error determining current network: {str(e)}", 'ERROR')
            self.logger.log(f"[ClipboardImageEXT] Error determining network: {str(e)}")
            # Fallback to parent
            return self.ownerComp.parent()
        
    def check_clipboard(self):
        """
        Quickly check if there's an image in the clipboard
        Displays a message and returns True if there's an image, False otherwise
        Example of using has_clipboard_image method
        """
        if self.ownerComp.par.Bypass.eval():
            return False
            
        # Check if there's an image in the clipboard
        has_image = self.has_clipboard_image()
        
        # Show message with result
        if has_image:
            message = "Image found in clipboard"
            self.logger.log(message, 'INFO')
            ui.status = message
        else:
            message = "No image found in clipboard"
            self.logger.log(message, 'INFO')
            ui.status = message
            
        return has_image
        
    def OnShortcut(self, shortcutName=None):
        if self.ownerComp.par.Bypass.eval():
            return
        if not self.check_clipboard():
            debug('[ClipboardImageEXT] No image found in clipboard')
            return
        # choice = ui.messageBox(title, message, buttons=options)
        self.popMenu.Open(callback=self.OnPopMenuCallback)

    def OnPopMenuShortcut(self, keyInfo):
        if keyInfo.state == True:
            key = keyInfo.key

            # look up the key in the PopMenuItemsShortcuts dictionary values
            for item, shortcut in self.PopMenuItemsShortcuts.items():
                if shortcut == key:
                    self.OnPopMenuCallback(item)

    def OnPopMenuCallback(self, infoDict):
        if isinstance(infoDict, str):
            choice = infoDict
        else:
            choice = infoDict['item']
            
        if choice == 'File In':
            self.Pasteimage()
        elif choice == 'ScriptTOP':
            self.Pastescriptop()
        elif choice == 'Annotate':
            self.Pasteannotate()

        self.popMenu.Close()
        