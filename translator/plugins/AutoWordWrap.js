//=============================================================================
// AutoWordWrap.js
//=============================================================================
/*:
 * @target MZ
 * @plugindesc Auto Word Wrap for Message Window (RPG Maker MZ)
 * @author VN RPG Translator
 *
 * @help
 * Automatically wraps words in the message window when text approaches
 * the right margin, preventing text from clipping outside the window.
 *
 * Installation:
 * 1. Copy this file into your game's js/plugins/ directory.
 * 2. Add AutoWordWrap to your game's js/plugins.js file, or enable it
 *    via RPG Maker MZ editor's Plugin Manager.
 */

(() => {
    const _Window_Message_processCharacter = Window_Message.prototype.processCharacter;
    Window_Message.prototype.processCharacter = function(textState) {
        const maxWidth = this.innerWidth - 16;
        const c = textState.text[textState.index];

        if (c === " ") {
            const remaining = textState.text.slice(textState.index + 1);
            const nextWordMatch = remaining.match(/^[^\s\x1b\n]+/);
            if (nextWordMatch) {
                const nextWord = nextWordMatch[0];
                const nextWordWidth = this.textWidth(nextWord);
                const currentWidth = textState.x + this.textWidth(textState.buffer);
                if (currentWidth + nextWordWidth + this.textWidth(" ") > maxWidth) {
                    textState.index++; // skip space
                    this.flushTextState(textState);
                    this.processNewLine(textState);
                    return;
                }
            }
        } else if (c && c.charCodeAt(0) >= 0x20) {
            const currentWidth = textState.x + this.textWidth(textState.buffer + c);
            if (currentWidth > maxWidth && textState.buffer.length > 0) {
                this.flushTextState(textState);
                this.processNewLine(textState);
            }
        }

        _Window_Message_processCharacter.call(this, textState);
    };
})();
