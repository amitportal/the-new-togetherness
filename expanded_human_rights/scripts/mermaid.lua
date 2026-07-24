-- mermaid.lua
-- Pandoc Lua filter to render Mermaid diagrams using mermaid-cli (mmdc)

function CodeBlock(block)
  if block.classes[1] == "mermaid" then
    -- Unique filename based on time
    local fname = "mermaid-" .. os.time() .. ".svg"
    local tmpfile = "diagram.mmd"

    -- Write diagram source to temp file
    local f = io.open(tmpfile, "w")
    f:write(block.text)
    f:close()

    -- Call mermaid-cli (mmdc) to render SVG
    os.execute("mmdc -i " .. tmpfile .. " -o " .. fname)

    -- Replace code block with image
    return pandoc.Para{ pandoc.Image({}, fname) }
  end
end

-- -- mermaid.lua
-- function CodeBlock(block)
--   if block.classes:includes("mermaid") then
--     local hash = pandoc.utils.sha1(block.text)
--     local mmd = "diagram-" .. hash .. ".mmd"
--     local svg = "diagram-" .. hash .. ".svg"

--     local f = io.open(mmd, "w")
--     f:write(block.text)
--     f:close()

--     os.execute("mmdc -i " .. mmd .. " -o " .. svg .. " -b transparent")

--     return pandoc.Para{
--       pandoc.Image({pandoc.Str("Figure: Mermaid diagram")}, svg)
--     }
--   end
-- end
